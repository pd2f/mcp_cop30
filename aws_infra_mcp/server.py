"""Model Context Protocol server exposing AWS infrastructure tools."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import boto3
from boto3.session import Session
from botocore.exceptions import BotoCoreError, ClientError
from fastmcp import FastMCP


LOGGER = logging.getLogger(__name__)


app = FastMCP(
    name="aws-infra",
    version="0.1.0",
    description=(
        "Expose ferramentas MCP para explorar os principais recursos de infraestrutura "
        "AWS, incluindo EC2, S3, RDS e inventário de contas."
    ),
)


@dataclass(slots=True)
class AwsResource:
    """Representação serializável de um recurso AWS retornado pelas ferramentas."""

    kind: str
    identifier: str
    data: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["data"] = _stringify_datetimes(payload["data"])
        return payload


def _stringify_datetimes(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_stringify_datetimes(item) for item in value]
    if isinstance(value, dict):
        return {key: _stringify_datetimes(val) for key, val in value.items()}
    return value


def _aws_session(region: Optional[str], profile: Optional[str]) -> Session:
    try:
        return boto3.Session(region_name=region, profile_name=profile)
    except Exception as error:  # pragma: no cover - boto3 levanta RuntimeError sem subclasses
        LOGGER.exception("Falha ao criar sessão AWS")
        raise RuntimeError(f"Não foi possível criar sessão AWS: {error}") from error


def _text_response(title: str, resources: Iterable[AwsResource]) -> Dict[str, Any]:
    payload = {
        "title": title,
        "resources": [resource.to_json() for resource in resources],
    }
    formatted = json.dumps(payload, indent=2, ensure_ascii=False)
    return {"content": [{"type": "text", "text": formatted}]}


def _error_response(message: str) -> Dict[str, Any]:
    return {"is_error": True, "content": [{"type": "text", "text": message}]}


def _handle_boto_error(error: Exception) -> Dict[str, Any]:
    LOGGER.exception("Erro durante chamada AWS")
    if isinstance(error, ClientError):
        message = error.response.get("Error", {}).get("Message", str(error))
    elif isinstance(error, BotoCoreError):
        message = str(error)
    else:
        message = str(error)
    return _error_response(f"Falha ao consultar AWS: {message}")


def _collect_ec2(
    session: Session,
    *,
    state: Optional[str] = None,
) -> List[AwsResource]:
    client = session.client("ec2")
    params: Dict[str, Any] = {}
    if state:
        params["Filters"] = [{"Name": "instance-state-name", "Values": [state]}]
    response = client.describe_instances(**params)
    resources: List[AwsResource] = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            resources.append(
                AwsResource(
                    kind="ec2_instance",
                    identifier=instance.get("InstanceId", "unknown"),
                    data={
                        "state": instance.get("State", {}).get("Name"),
                        "type": instance.get("InstanceType"),
                        "launch_time": instance.get("LaunchTime"),
                        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                        "public_ip": instance.get("PublicIpAddress"),
                        "tags": instance.get("Tags", []),
                    },
                )
            )
    return resources


@app.tool(
    name="listar_ec2",
    description=(
        "Lista instâncias EC2. Filtre por estado com o parâmetro opcional 'state'. "
        "Pode receber 'region' e 'profile'."
    ),
)
def list_ec2_instances(
    region: Optional[str] = None,
    profile: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    try:
        session = _aws_session(region, profile)
        resources = _collect_ec2(session, state=state)
        return _text_response("Instâncias EC2", resources)
    except Exception as error:  # pragma: no cover - boto3 erros tratados genericamente
        return _handle_boto_error(error)


def _collect_s3(session: Session) -> List[AwsResource]:
    client = session.client("s3")
    response = client.list_buckets()
    return [
        AwsResource(
            kind="s3_bucket",
            identifier=bucket.get("Name", "unknown"),
            data={"creation_date": bucket.get("CreationDate")},
        )
        for bucket in response.get("Buckets", [])
    ]


@app.tool(
    name="listar_buckets_s3",
    description="Lista buckets S3 disponíveis na conta. Pode receber 'profile'.",
)
def list_s3_buckets(region: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    try:
        session = _aws_session(region, profile)
        resources = _collect_s3(session)
        return _text_response("Buckets S3", resources)
    except Exception as error:  # pragma: no cover
        return _handle_boto_error(error)


def _collect_rds(session: Session) -> List[AwsResource]:
    client = session.client("rds")
    response = client.describe_db_instances()
    return [
        AwsResource(
            kind="rds_instance",
            identifier=db.get("DBInstanceIdentifier", "unknown"),
            data={
                "engine": db.get("Engine"),
                "status": db.get("DBInstanceStatus"),
                "instance_class": db.get("DBInstanceClass"),
                "endpoint": db.get("Endpoint", {}).get("Address"),
                "multi_az": db.get("MultiAZ"),
            },
        )
        for db in response.get("DBInstances", [])
    ]


@app.tool(
    name="listar_rds",
    description="Lista instâncias RDS. Pode receber 'region' e 'profile'.",
)
def list_rds_instances(region: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    try:
        session = _aws_session(region, profile)
        resources = _collect_rds(session)
        return _text_response("Instâncias RDS", resources)
    except Exception as error:  # pragma: no cover
        return _handle_boto_error(error)


@app.tool(
    name="resumo_conta",
    description=(
        "Resumo rápido da conta AWS utilizando listas de recursos suportados. "
        "Recebe os mesmos parâmetros de região/perfil das outras ferramentas."
    ),
)
def summarize_account(region: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    try:
        session = _aws_session(region, profile)
        summary = {
            "ec2_instances": len(_collect_ec2(session, state=None)),
            "s3_buckets": len(_collect_s3(session)),
            "rds_instances": len(_collect_rds(session)),
        }
        formatted = json.dumps(summary, indent=2, ensure_ascii=False)
        return {"content": [{"type": "text", "text": formatted}]}
    except Exception as error:  # pragma: no cover
        return _handle_boto_error(error)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app.run()


__all__ = ["app", "main"]
