from shiny import App, ui, reactive,render
import requests as req
import os

welcome = ui.markdown("""Olá! Sou a cceelabs, Bem vindo ao ambiente de experimentações com interface conversacional.""")


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_selectize(
            "use_case",
            "Escolha a Aplicação",
            choices=[
                "Workshop",
                "MCP de Bolso",
                # "Grupo 2",
                # "Grupo 3",
                # "Grupo 4",
                # "Grupo 5",
            ],
            selected="MCP de Bolso",
        ),               
        ui.panel_conditional(
        "input.use_case === 'Workshop'",
        ui.input_selectize(
            "funcionalidade",
            "Escolha a funcionalidade",
            choices=[
                "FM (LLM)",
                "Web",
                "RAG (RHAI)",
                "Agentic (Dados Abertos)"
            ],
            selected="Web",
        ),       
        ui.tooltip(ui.input_switch(id="guardrail", label="Guard Rail", value=False,width='150px'),"Limitação de conteúdo para resposta da IA",id="info_guardrail"),
        ),
        # ui.input_action_button(
        #     "aplicar",
        #     "Play",
        #     # icon=icon_svg("play"),
        #     class_="btn btn-primary",
        # ),
        ui.panel_conditional(
        "input.use_case === 'Falta Implementar'",
        ui.tooltip(ui.input_slider(
                id="temperatura",
                label="Temperatura",
                min=0,
                max=1,
                value=0,
                step=0.1),"Quanto menor o valor, mais determinístico. Quanto maior o valor, mais estocástico 'criativo'")),
        ui.panel_conditional(
            "input.use_case !== 'MCP de Bolso'",
        ui.input_text_area(id="system_prompt",
            label="System Prompt",
            # cols=200,
            rows=3,
            placeholder="Insira um texto para primeira orientação da GenAI. Comportamento, forma de raciocinar, exemplos e outras instruções que a ajudem a atender as suas expectativas.",
            autoresize=True),
        id="sidebar",width="25%"
    )), 
    ui.chat_ui(id="chat",placeholder="Digite a sua mensagem...",messages=[welcome],height="20%", fill=True,show=False),
    title="Experimentações cceelabs",
    # fillable=True,
    # fillable_mobile=True,
    style="height:100%",
)


def opcao(funcionalidade,use_case,guardrail):
    service = funcionalidade
    grupo = ""
    if use_case != 'Workshop':
        grupo = "/"+str(use_case)[0]+str(use_case)[-1]
        service = "rag"
        
    if use_case == 'MCP de Bolso':
        grupo = ""
        service = "Agentic (Dados Abertos)"
    
    if service == "FM (LLM)":
        service = "llm"
    guardrail = "**sem** Guard Rail" if (guardrail==False and use_case == 'Workshop')  else "**com** Guard Rail"
    return service,grupo,use_case,guardrail

def server(input, output, session):
    chat = ui.Chat(id="chat")
    val = reactive.value('*configuração pendente')
    has_started: reactive.value[bool] = reactive.value(False)
    
    @render.text
    def value():
        return str(val.get())

    # # Quando o usuário clica no botão 'play'
    # @reactive.effect
    # @reactive.event(input.aplicar)
    # async def _():
    #     if has_started():
    #         await chat.clear_messages()
    #         await chat.append_message(welcome)
    #         ui.update_sidebar("sidebar", show=False)
    #     service,_,grupo,guardrail = opcao(input.funcionalidade(),input.use_case(),input.guardrail())
    #     # await chat.append_message(f"Sua configuração de uso é: {service} para {grupo} {guardrail}")
    #     chat.update_user_input(value="", focus=True)
    #     has_started.set(True)
        
        

    # Apresentar painel lateral quanto carregar a página    
    @reactive.effect
    async def _():
        if has_started():
            ui.update_sidebar("sidebar", show=True)
            ui.update_action_button("aplicar", label="Play")

    # Função que responde de submissão da mensagem do usuário
    @chat.on_user_submit
    async def _():
        ui.update_sidebar("sidebar", show=False)
        user = chat.user_input()       
        service,grupo,_,_ = opcao(input.funcionalidade(),input.use_case(),input.guardrail())
        if service == "RAG (RHAI)":
            service="rag"
        if service == "Agentic (Dados Abertos)":
            service="agentic"
            grupo = ""
        parametro=""
        if input.guardrail():
            parametro="?guardrail=true"
        if service == "agentic":
            url = os.getenv("ENDPOINT_BACKEND")+"{funcionalidade}".format(funcionalidade=str(service).lower())
        else:
            url = os.getenv("ENDPOINT_BACKEND")+"{funcionalidade}{workshop}{parametro}".format(funcionalidade=str(service).lower(),workshop=grupo.lower(),parametro=parametro)
            
        payload = dict(messages=[dict(human=user)],metadata=dict(temperature=input.temperatura()))
        if input.system_prompt() is not None:
            payload = dict(messages=[dict(human=user,system=input.system_prompt())],metadata=dict(temperature=input.temperatura()))
        payload = dict(payload = payload)
        res = req.post(url,json=payload)
        res = res.json().replace("\\n","<br/>")
        await chat.append_message('cceelabs: {resposta}'.format(resposta=res))
    
app = App(app_ui, server)
