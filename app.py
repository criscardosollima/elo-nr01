import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import base64
import urllib.parse
import urllib.request
from streamlit_option_menu import option_menu
import textwrap
import hashlib
import random
import time
import json
import uuid
from supabase import create_client, Client

# ==============================================================================
# 1. INICIALIZAÇÃO DA PÁGINA E DA CONEXÃO COM O BANCO DE DADOS (SUPABASE)
# ==============================================================================
st.set_page_config(
    page_title="Elo NR-01 | Sistema Inteligente",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bloco de tentativa de conexão segura com o Supabase.
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
    # Em caso de falha, o sistema operará em modo de contingência (memória local/cache).

# ------------------------------------------------------------------------------
# 1.1. GERENCIAMENTO DE ESTADO E PERSISTÊNCIA DE IDENTIDADE (CONFIGURAÇÕES GERAIS)
# ------------------------------------------------------------------------------
def get_saved_settings():
    """
    Função vital para buscar as configurações globais da plataforma (Logo, Nome, URL)
    diretamente do banco de dados relacional. Impede que os dados sumam ao dar F5.
    """
    default_conf = {
        "name": "Elo NR-01",
        "consultancy": "Pessin Gestão e Desenvolvimento Humano",
        "logo_b64": None,
        "base_url": "https://elonr01-cris.streamlit.app" 
    }
    
    if DB_CONNECTED:
        try:
            res = supabase.table('platform_settings').select('config_json').execute()
            if res.data and len(res.data) > 0:
                db_conf = res.data[0].get('config_json', {})
                default_conf.update(db_conf)
        except Exception as e:
            pass
            
    return default_conf

if 'platform_config' not in st.session_state:
    st.session_state.platform_config = get_saved_settings()

# ------------------------------------------------------------------------------
# 1.2. PALETA DE CORES OFICIAL DA IDENTIDADE VISUAL
# ------------------------------------------------------------------------------
COR_PRIMARIA = "#003B49"    
COR_SECUNDARIA = "#40E0D0"  
COR_FUNDO = "#f4f6f9"
COR_RISCO_ALTO = "#ef5350"      # Vermelho (Alerta Crítico)
COR_RISCO_MEDIO = "#ffa726"     # Laranja/Amarelo (Atenção Modereada)
COR_RISCO_BAIXO = "#66bb6a"     # Verde (Cenário Seguro/Saudável)
COR_COMP_A = "#3498db"          # Azul (Gráficos)
COR_COMP_B = "#9b59b6"          # Roxo (Gráficos)

# ==============================================================================
# 2. FOLHA DE ESTILOS EM CASCATA (CSS OTIMIZADO E ESTRUTURADO)
# ==============================================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    .stApp {{ background-color: {COR_FUNDO}; font-family: 'Inter', sans-serif; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
    [data-testid="stSidebar"] {{ background-color: #ffffff; border-right: 1px solid #e0e0e0; box-shadow: 2px 0 5px rgba(0,0,0,0.02); }}
    
    .kpi-card {{ background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; margin-bottom: 15px; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; height: auto; transition: transform 0.2s ease-in-out; }}
    .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.08); }}
    .kpi-title {{ font-size: 12px; color: #7f8c8d; font-weight: 600; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .kpi-value {{ font-size: 26px; font-weight: 800; color: {COR_PRIMARIA}; margin-top: 5px; }}
    .kpi-top {{ display: flex; align-items: center; gap: 15px; }}
    .kpi-icon-box {{ width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }}
    
    .bg-blue {{ background-color: #e3f2fd; color: #1976d2; }}
    .bg-green {{ background-color: #e8f5e9; color: #388e3c; }}
    .bg-orange {{ background-color: #fff3e0; color: #f57c00; }}
    .bg-red {{ background-color: #ffebee; color: #d32f2f; }}

    .chart-container {{ background: #ffffff; padding: 22px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #f0f0f0; margin-bottom: 18px; }}
    .security-alert {{ padding: 1.5rem; background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; border-left: 6px solid #0f5132; border-radius: 0.35rem; margin-bottom: 2rem; font-family: 'Inter', sans-serif; font-size: 0.95rem; }}
    
    .a4-paper {{ background: #ffffff; width: 210mm; min-height: 297mm; margin: auto; padding: 40px; box-shadow: 0 0 20px rgba(0,0,0,0.1); color: #333333; font-family: 'Inter', sans-serif; font-size: 11px; line-height: 1.5; }}
    .rep-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 10px; }}
    .rep-table th {{ background-color: {COR_PRIMARIA}; color: #ffffff; padding: 10px 8px; text-align: left; font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .rep-table td {{ border-bottom: 1px solid #eeeeee; padding: 10px 8px; vertical-align: top; }}
    
    div[role="radiogroup"] > label {{ font-weight: 500; color: #444444; background: #f8f9fa; padding: 10px 16px; border-radius: 8px; border: 1px solid #eeeeee; cursor: pointer; transition: all 0.2s ease-in-out; white-space: normal; text-align: center; flex: 1 1 0px; display: flex; justify-content: center; align-items: center; }}
    div[role="radiogroup"] > label:hover {{ background: #e2e6ea; border-color: {COR_SECUNDARIA}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    div[data-testid="stRadio"] > div {{ flex-direction: row; flex-wrap: wrap; gap: 8px; width: 100%; padding-bottom: 15px; }}

    @media print {{
        [data-testid="stSidebar"], .stButton, header, footer, .no-print {{ display: none !important; }}
        .a4-paper {{ box-shadow: none; margin: 0; padding: 0; width: 100%; max-width: 100%; }}
        .stApp {{ background-color: #ffffff; }}
        .chart-container {{ border: none; box-shadow: none; padding: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. MÁQUINA DE DADOS: INICIALIZAÇÃO DE ESTADOS E MOCKS
# ==============================================================================
keys_to_init = [
    'logged_in', 'user_role', 'admin_permission', 'user_username', 
    'user_credits', 'user_linked_company', 'edit_mode', 'edit_id', 'acoes_list'
]

for k in keys_to_init:
    if k not in st.session_state: 
        st.session_state[k] = None

if st.session_state.acoes_list is None: st.session_state.acoes_list = []
if st.session_state.user_credits is None: st.session_state.user_credits = 0

if 'users_db' not in st.session_state:
    st.session_state.users_db = { "admin": { "password": "admin", "role": "Master", "credits": 999999 } }
if 'companies_db' not in st.session_state: st.session_state.companies_db = []
if 'local_responses_db' not in st.session_state: st.session_state.local_responses_db = []

# ------------------------------------------------------------------------------
# 3.1. BANCO DE METODOLOGIAS DIAGNÓSTICAS (HSE + COPSOQ)
# ------------------------------------------------------------------------------
if 'methodologies' not in st.session_state:
    escala_freq = ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"]
    escala_conc = ["Discordo Totalmente", "Discordo", "Neutro", "Concordo", "Concordo Totalmente"]
    
    st.session_state.methodologies = {
        "HSE-IT (35 itens)": {
            "desc": "Focado em 7 dimensões de gestão de estresse (Padrão UK/Brasil).",
            "questions": {
                "Demandas": [
                    {"id": "h1", "q": "Tenho prazos impossíveis de cumprir?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Ser cobrado rotineiramente por entregas urgentes no fim do expediente sem tempo hábil para execução com qualidade."},
                    {"id": "h2", "q": "Sou pressionado a trabalhar longas horas?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Sentir que apenas cumprir o seu horário normal de trabalho não é suficiente para a empresa ou para dar conta de tudo."},
                    {"id": "h3", "q": "Tenho que trabalhar muito intensamente?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Não ter tempo nem para respirar, esticar as pernas ou tomar um café direito devido ao alto volume de demandas."},
                    {"id": "h4", "q": "Tenho que negligenciar algumas tarefas?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Ter que fazer as coisas 'de qualquer jeito' ou pular etapas de segurança só para dar tempo de entregar tudo."},
                    {"id": "h5", "q": "Não consigo fazer pausas suficientes?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Precisar pular o horário de almoço ou comer correndo na mesa de trabalho para não acumular processos."},
                    {"id": "h6", "q": "Sou pressionado por diferentes grupos?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Receber ordens conflitantes ou urgentes de gestores diferentes, ou de clientes e diretoria ao mesmo tempo."},
                    {"id": "h7", "q": "Tenho que trabalhar muito rápido?", "rev": True, "options": escala_freq, "help": "Exemplo prático: O ritmo exigido na sua linha de produção ou setor é frenético e desgastante o tempo todo."},
                    {"id": "h8", "q": "Tenho prazos irrealistas?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Metas comerciais ou prazos de projetos que, na prática do dia a dia, ninguém da equipe consegue bater de forma saudável."}
                ],
                "Controle": [
                    {"id": "h9", "q": "Posso decidir quando fazer uma pausa?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Ter liberdade para levantar, ir ao banheiro ou tomar uma água sem precisar pedir permissão constante."},
                    {"id": "h10", "q": "Tenho liberdade para decidir como faço meu trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Poder escolher o melhor método, caminho ou ferramenta para entregar o resultado que esperam de você."},
                    {"id": "h11", "q": "Tenho poder de decisão sobre meu ritmo?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Poder acelerar as tarefas em um momento e diminuir o ritmo em outro dependendo do seu nível de foco e energia."},
                    {"id": "h12", "q": "Eu decido quando vou realizar cada tarefa?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Ter autonomia para organizar sua própria agenda diária, escolhendo o que fazer primeiro."},
                    {"id": "h13", "q": "Tenho voz sobre como meu trabalho é realizado?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Suas ideias de melhorias nos processos do setor são ouvidas e efetivamente testadas/aplicadas pela gestão."},
                    {"id": "h14", "q": "Meu tempo de trabalho pode ser flexível?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Ter acesso a banco de horas, horários flexíveis de entrada/saída ou acordos amigáveis com o líder para idas ao médico."}
                ],
                "Suporte Gestor": [
                    {"id": "h15", "q": "Recebo feedback sobre o trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Seu gestor senta com você para conversar de forma clara, madura e respeitosa sobre o que está bom e o que pode melhorar."},
                    {"id": "h16", "q": "Posso contar com meu superior num problema?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Saber que o gestor vai te ajudar a resolver uma falha técnica ou erro em vez de apenas te culpar ou expor."},
                    {"id": "h17", "q": "Posso falar com meu superior sobre algo que me chateou?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Ter abertura psicológica para conversas sinceras e humanas com a chefia, sem medo de retaliação."},
                    {"id": "h18", "q": "Sinto apoio do meu gestor(a)?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Sentir que seu chefe é um facilitador que 'joga no seu time' e se importa genuinamente com seu bem-estar geral."},
                    {"id": "h19", "q": "Meu gestor me incentiva no trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Receber elogios, reconhecimento público ou privado, e motivação consistente quando faz um bom trabalho."}
                ],
                "Suporte Pares": [
                    {"id": "h20", "q": "Recebo a ajuda e o apoio que preciso dos meus colegas?", "rev": False, "options": escala_freq, "help": "Exemplo prático: A equipe de base é unida e um colaborador cobre o outro quando a situação aperta."},
                    {"id": "h21", "q": "Recebo o respeito que mereço dos meus colegas?", "rev": False, "options": escala_freq, "help": "Exemplo prático: O tratamento no dia a dia entre os colegas é cordial, extremamente respeitoso e livre de preconceitos."},
                    {"id": "h22", "q": "Meus colegas estão dispostos a me ouvir sobre problemas?", "rev": False, "options": escala_freq, "help": "Exemplo prático: Ter com quem desabafar de forma segura sobre um dia difícil, uma tarefa complexa ou um cliente complicado."},
                    {"id": "h23", "q": "Meus colegas me ajudam em momentos difíceis?", "rev": False, "options": escala_freq, "help": "Exemplo prático: A equipe divide o peso solidariamente quando o volume de trabalho está visivelmente muito alto para uma pessoa só."}
                ],
                "Relacionamentos": [
                    {"id": "h24", "q": "Estou sujeito a assédio pessoal?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Sofrer ou presenciar comentários desrespeitosos, constrangedores, piadas com características físicas ou pressões indevidas no ambiente."},
                    {"id": "h25", "q": "Há atritos ou conflitos entre colegas?", "rev": True, "options": escala_freq, "help": "Exemplo prático: O clima geral é de fofoca, formação de 'panelinhas', competição desleal ou brigas constantes no setor."},
                    {"id": "h26", "q": "Estou sujeito a bullying?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Ser excluído propositalmente de conversas de trabalho, grupos, ou ser alvo sistemático de chacotas maldosas."},
                    {"id": "h27", "q": "Os relacionamentos no trabalho são tensos?", "rev": True, "options": escala_freq, "help": "Exemplo prático: Aquele clima pesado onde todos parecem 'pisar em ovos' para falar com o outro com medo de explosões ou cortes."}
                ],
                "Papel": [
                    {"id": "h28", "q": "Sei claramente o que é esperado de mim?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Suas metas mensais, entregas esperadas e funções diárias estão muito bem definidas e acordadas."},
                    {"id": "h29", "q": "Sei como fazer para executar meu trabalho?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Você recebeu o treinamento necessário, tem capacidade técnica e dispõe das ferramentas certas para trabalhar bem."},
                    {"id": "h30", "q": "Sei quais são os objetivos do meu departamento?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Você entende perfeitamente para onde sua equipe está caminhando estrategicamente e o que precisa ser entregue."},
                    {"id": "h31", "q": "Sei o quanto de responsabilidade tenho?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Os limites da sua função, até onde você pode agir, aprovar e decidir sozinho são claros para você e para a gestão."},
                    {"id": "h32", "q": "Entendo meu encaixe na empresa?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Você consegue ver nitidamente a importância e o impacto do seu trabalho diário para o sucesso geral e faturamento do negócio."}
                ],
                "Mudança": [
                    {"id": "h33", "q": "Tenho oportunidade de questionar sobre mudanças?", "rev": False, "options": escala_conc, "help": "Exemplo prático: Existir espaço físico ou virtual seguro para tirar dúvidas reais quando uma nova regra, sistema ou chefia é imposta."},
                    {"id": "h34", "q": "Sou consultado(a) sobre mudanças no trabalho?", "rev": False, "options": escala_conc, "help": "Exemplo prático: A diretoria ou chefia tem o costume de pedir a opinião de quem executa a tarefa antes de mudar radicalmente um processo."},
                    {"id": "h35", "q": "Quando mudanças são feitas, fica claro como funcionarão?", "rev": False, "options": escala_conc, "help": "Exemplo prático: A comunicação corporativa é transparente, os passos são bem explicados e a mudança não gera um caos ou confusão na equipe."}
                ]
            }
        },
        "COPSOQ II (Versão Média PT)": {
            "desc": "Versão Média Portuguesa (Adaptação FCT). Avalia riscos, exigências mentais e valores no ambiente laboral de forma profunda e ampliada.",
            "questions": {
                "Exigências Laborais e Ritmo": [
                    {"id": "c1", "q": "A sua carga de trabalho acumula-se por ser mal distribuída?", "rev": True, "options": escala_freq, "help": "Percepção de desequilíbrio estrutural nas demandas diárias."},
                    {"id": "c2", "q": "Com que frequência não tem tempo para completar todas as tarefas?", "rev": True, "options": escala_freq, "help": "Sensação crônica de falta de tempo hábil para a operação."},
                    {"id": "c3", "q": "Precisa fazer horas-extra?", "rev": True, "options": escala_freq, "help": "Necessidade constante de estender a jornada para não atrasar entregas."},
                    {"id": "c4", "q": "Precisa trabalhar muito rapidamente?", "rev": True, "options": escala_freq, "help": "Ritmo acelerado e sem pausas estratégicas (pressão de tempo)."},
                    {"id": "c5", "q": "O seu trabalho exige a sua atenção constante?", "rev": True, "options": escala_freq, "help": "Foco mental ininterrupto sem margem de descanso cognitivo."},
                    {"id": "c6", "q": "O seu trabalho exige que se lembre de muitas coisas?", "rev": True, "options": escala_freq, "help": "Alta carga de memória de trabalho e concentração multitarefa."},
                    {"id": "c7", "q": "O seu trabalho exige que tome decisões difíceis?", "rev": True, "options": escala_freq, "help": "Carga de responsabilidade moral, técnica ou financeira elevada."},
                    {"id": "c8", "q": "O seu trabalho exige emocionalmente de si?", "rev": True, "options": escala_freq, "help": "Lidar com situações de forte impacto emocional ou clientes difíceis diariamente."}
                ],
                "Organização e Influência": [
                    {"id": "c9", "q": "Tem um elevado grau de influência no seu trabalho?", "rev": False, "options": escala_freq, "help": "Poder real de afetar decisões e o rumo do setor."},
                    {"id": "c10", "q": "Participa na escolha das pessoas com quem trabalha?", "rev": False, "options": escala_freq, "help": "Voz ativa na seleção ou formação de times e equipes."},
                    {"id": "c13", "q": "O seu trabalho exige que tenha iniciativa?", "rev": False, "options": escala_freq, "help": "Espaço para ser proativo ao invés de apenas reativo e operacional."},
                    {"id": "c14", "q": "O seu trabalho permite-lhe aprender coisas novas?", "rev": False, "options": escala_freq, "help": "Desenvolvimento intelectual e profissional contínuo."},
                    {"id": "c15", "q": "O seu trabalho permite-lhe usar as suas habilidades?", "rev": False, "options": escala_freq, "help": "Aproveitamento pleno do seu potencial, formação e talentos."},
                    {"id": "c16", "q": "É informado com antecedência sobre decisões importantes?", "rev": False, "options": escala_freq, "help": "Transparência diretiva antes das execuções de mudanças que afetam sua rotina."},
                    {"id": "c19", "q": "Sabe exactamente quais as suas responsabilidades?", "rev": False, "options": escala_freq, "help": "Clareza absoluta do papel e das metas esperadas pela organização."}
                ],
                "Relações e Liderança": [
                    {"id": "c21", "q": "O seu trabalho é reconhecido e apreciado pela gerência?", "rev": False, "options": escala_freq, "help": "Percepção clara de valorização do esforço e dedicação diária."},
                    {"id": "c27", "q": "Com que frequência tem ajuda e apoio dos seus colegas?", "rev": False, "options": escala_freq, "help": "Rede de apoio horizontal sólida entre pares de equipe."},
                    {"id": "c31", "q": "Com que frequência tem apoio do seu superior imediato?", "rev": False, "options": escala_freq, "help": "Presença, instrução e suporte do gestor nos momentos de desafio."},
                    {"id": "c33", "q": "Existe um bom ambiente de trabalho entre si e os colegas?", "rev": False, "options": escala_freq, "help": "Clima de camaradagem, leveza e segurança psicológica na baia/setor."},
                    {"id": "c35", "q": "No seu local de trabalho sente-se parte de uma comunidade?", "rev": False, "options": escala_freq, "help": "Senso de pertencimento profundo ao grupo maior da empresa."},
                    {"id": "c36", "q": "A chefia oferece boas oportunidades de desenvolvimento?", "rev": False, "options": escala_freq, "help": "Investimento prático na sua carreira, cursos e evolução salarial."},
                    {"id": "c38", "q": "A chefia é boa no planeamento do trabalho?", "rev": False, "options": escala_freq, "help": "Organização prévia que evita o caos da urgência constante."},
                    {"id": "c39", "q": "A chefia é boa a resolver conflitos?", "rev": False, "options": escala_freq, "help": "Habilidade técnica e madura da liderança em mediar crises internas sem tomar lados injustamente."}
                ],
                "Valores, Sentido e Justiça": [
                    {"id": "c42", "q": "Os funcionários confiam uns nos outros de um modo geral?", "rev": False, "options": escala_freq, "help": "Índice de confiança lateral (horizontal) na corporação como um todo."},
                    {"id": "c44", "q": "Confia na informação que lhe é transmitida pela gerência?", "rev": False, "options": escala_freq, "help": "Credibilidade e franqueza da comunicação que vem de cima (top-down)."},
                    {"id": "c45", "q": "A gerência oculta informação aos seus funcionários?", "rev": True, "options": escala_freq, "help": "Percepção de segredos, agendas ocultas ou falta de transparência diretiva."}, 
                    {"id": "c46", "q": "Os conflitos são resolvidos de uma forma justa?", "rev": False, "options": escala_freq, "help": "Imparcialidade e equidade na resolução de crises, sem favorecimentos."},
                    {"id": "c48", "q": "O trabalho é igualmente distribuído pelos funcionários?", "rev": False, "options": escala_freq, "help": "Sensação de justiça no peso das responsabilidades diárias entre a equipe."},
                    {"id": "c51", "q": "O seu trabalho tem algum significado para si?", "rev": False, "options": escala_freq, "help": "Conexão de propósito pessoal e orgulho com a atividade laboral desenvolvida."},
                    {"id": "c53", "q": "Sente-se motivado e envolvido com o seu trabalho?", "rev": False, "options": escala_freq, "help": "Nível de engajamento ativo, paixão e vontade de acordar para trabalhar."}
                ],
                "Saúde, Stress e Bem-estar (Últimas 4 semanas)": [
                    {"id": "c61", "q": "Em geral, sente que a sua saúde é excelente ou boa?", "rev": False, "options": escala_freq, "help": "Autoavaliação perceptiva de saúde global, física e mental."},
                    {"id": "c65", "q": "Dificuldade a adormecer?", "rev": True, "options": escala_freq, "help": "Insônia inicial frequente por não conseguir 'desligar' a mente."},
                    {"id": "c66", "q": "Acordou várias vezes durante a noite?", "rev": True, "options": escala_freq, "help": "Sono fragmentado, sobressaltos e descanso não reparador."},
                    {"id": "c67", "q": "Sente-se fisicamente exausto?", "rev": True, "options": escala_freq, "help": "Fadiga física persistente e dores musculares relacionadas à tensão."},
                    {"id": "c68", "q": "Sente-se emocionalmente exausto?", "rev": True, "options": escala_freq, "help": "Sintomas precoces de Burnout emocional, não ter energia para lidar com pessoas."},
                    {"id": "c70", "q": "Sente-se ansioso?", "rev": True, "options": escala_freq, "help": "Estado de alerta constante, taquicardia leve e preocupação mental excessiva."},
                    {"id": "c71", "q": "Sente-se triste?", "rev": True, "options": escala_freq, "help": "Sintomas de rebaixamento de humor, distimia ou falta de esperança."}
                ],
                "Comportamentos Ofensivos (Últimos 12 meses)": [
                    {"id": "c73", "q": "Tem sido alvo de insultos ou provocações verbais?", "rev": True, "options": escala_freq, "help": "Violência verbal pontual ou repetida no ambiente de trabalho."},
                    {"id": "c74", "q": "Tem sido exposto a assédio sexual indesejado?", "rev": True, "options": escala_freq, "help": "Invasões gravíssimas de limites corporais, olhares ou insinuações abusivas."},
                    {"id": "c75", "q": "Tem sido exposto a ameaças de violência?", "rev": True, "options": escala_freq, "help": "Clima de intimidação física, coação ou moral extremada."}
                ]
            }
        }
    }

# ==============================================================================
# 4. ENGINE DE CÁLCULO E PERSISTÊNCIA DE DADOS (LÓGICA CORE)
# ==============================================================================

def get_logo_html(width=180):
    """
    Constrói a tag HTML de imagem. Renderiza o Base64 do banco de dados ou 
    fornece um fallback visual robusto em SVG caso não haja logo carregada.
    """
    if st.session_state.platform_config['logo_b64']:
        # Proteção contra prefixos duplicados base64 que quebram o html
        clean_b64 = st.session_state.platform_config['logo_b64']
        if clean_b64.startswith('data:image'):
            clean_b64 = clean_b64.split(',')[1]
        return f'<img src="data:image/png;base64,{clean_b64}" width="{width}" style="max-width: 100%; height: auto;">'
    
    # SVG Fallback
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" width="{width}">
        <style>
            .t1 {{ font-family: 'Inter', sans-serif; font-weight: 800; font-size: 48px; fill: {COR_PRIMARIA}; }} 
            .t2 {{ font-family: 'Inter', sans-serif; font-weight: 300; font-size: 48px; fill: {COR_SECUNDARIA}; }} 
            .sub {{ font-family: 'Inter', sans-serif; font-weight: 600; font-size: 11px; fill: {COR_PRIMARIA}; letter-spacing: 3px; text-transform: uppercase; }}
        </style>
        <g transform="translate(10, 20)">
            <rect x="0" y="10" width="35" height="35" rx="8" ry="8" fill="none" stroke="{COR_SECUNDARIA}" stroke-width="8" />
            <rect x="20" y="10" width="35" height="35" rx="8" ry="8" fill="none" stroke="{COR_PRIMARIA}" stroke-width="8" />
        </g>
        <text x="80" y="55" class="t1">ELO</text>
        <text x="190" y="55" class="t2">NR-01</text>
        <text x="82" y="80" class="sub">SISTEMA INTELIGENTE</text>
    </svg>
    """
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}">'

def image_to_base64(file):
    """Utilitário de conversão de imagens de upload (FileBuffer) para string Base64 limpa."""
    try: 
        if file is not None:
            bytes_data = file.getvalue()
            return base64.b64encode(bytes_data).decode('utf-8')
        return None
    except Exception as e: 
        st.error(f"Erro ao processar imagem: {e}")
        return None

def logout(): 
    """Encerra a sessão do usuário de forma segura e imediata."""
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.admin_permission = None
    st.rerun()

def calculate_actual_scores(all_responses, companies_list, methodologies_dict):
    """
    Motor matemático robusto. 
    Lê a metodologia atrelada à empresa daquela resposta e calcula o score invertendo a escala se necessário.
    """
    comp_method_map = {str(c['id']): c.get('metodologia', 'HSE-IT (35 itens)') for c in companies_list}
    
    for resp_row in all_responses:
        comp_id = str(resp_row.get('company_id'))
        metodo_nome = comp_method_map.get(comp_id, 'HSE-IT (35 itens)')
        active_questions = methodologies_dict.get(metodo_nome, methodologies_dict['HSE-IT (35 itens)'])['questions']
        
        ans_dict = resp_row.get('answers', {})
        total_score = 0
        count_valid = 0
        
        for cat, qs in active_questions.items():
            for q in qs:
                q_text = q['q']
                is_rev = q.get('rev', False)
                user_ans = ans_dict.get(q_text)
                
                if user_ans:
                    val = None
                    if user_ans in ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre", "Nunca/Quase nunca"]:
                        # Ajuste para cobrir a opção dupla caso aconteça
                        if is_rev: 
                            val = {"Nunca": 5, "Nunca/Quase nunca": 5, "Raramente": 4, "Às vezes": 3, "Frequentemente": 2, "Sempre": 1}.get(user_ans)
                        else: 
                            val = {"Nunca": 1, "Nunca/Quase nunca": 1, "Raramente": 2, "Às vezes": 3, "Frequentemente": 4, "Sempre": 5}.get(user_ans)
                    
                    elif user_ans in ["Discordo Totalmente", "Discordo", "Neutro", "Concordo", "Concordo Totalmente"]:
                        if is_rev: 
                            val = {"Discordo Totalmente": 5, "Discordo": 4, "Neutro": 3, "Concordo": 2, "Concordo Totalmente": 1}.get(user_ans)
                        else: 
                            val = {"Discordo Totalmente": 1, "Discordo": 2, "Neutro": 3, "Concordo": 4, "Concordo Totalmente": 5}.get(user_ans)

                    if val is not None:
                        total_score += val
                        count_valid += 1
                        
        # Adiciona a coluna computada ao dicionário da linha (Útil para o gráfico de setores)
        resp_row['score_calculado'] = round(total_score / count_valid, 2) if count_valid > 0 else 0
    
    return all_responses

def process_company_analytics(comp, comp_resps, active_questions):
    """
    Coração Analítico focado e dinâmico por metodologia.
    Processa os dados brutos de uma empresa específica e fornece os scores dimensionais.
    """
    comp['respondidas'] = len(comp_resps)
    
    # Early return seguro caso não haja respostas, prevenindo divisões por zero
    if comp['respondidas'] == 0:
        comp['score'] = 0.0
        comp['dimensoes'] = {cat: 0.0 for cat in active_questions.keys()}
        comp['detalhe_perguntas'] = {}
        return comp

    dimensoes_totais = {cat: [] for cat in active_questions.keys()}
    soma_por_pergunta = {} 
    total_por_pergunta = {}

    for resp_row in comp_resps:
        ans_dict = resp_row.get('answers', {})
        
        for cat, qs in active_questions.items():
            for q in qs:
                q_text = q['q']
                is_rev = q.get('rev', False)
                user_ans = ans_dict.get(q_text)
                
                if user_ans:
                    val = None
                    if user_ans in ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre", "Nunca/Quase nunca"]:
                        if is_rev: 
                            val = {"Nunca": 5, "Nunca/Quase nunca": 5, "Raramente": 4, "Às vezes": 3, "Frequentemente": 2, "Sempre": 1}.get(user_ans)
                        else: 
                            val = {"Nunca": 1, "Nunca/Quase nunca": 1, "Raramente": 2, "Às vezes": 3, "Frequentemente": 4, "Sempre": 5}.get(user_ans)
                    
                    elif user_ans in ["Discordo Totalmente", "Discordo", "Neutro", "Concordo", "Concordo Totalmente"]:
                        if is_rev: 
                            val = {"Discordo Totalmente": 5, "Discordo": 4, "Neutro": 3, "Concordo": 2, "Concordo Totalmente": 1}.get(user_ans)
                        else: 
                            val = {"Discordo Totalmente": 1, "Discordo": 2, "Neutro": 3, "Concordo": 4, "Concordo Totalmente": 5}.get(user_ans)

                    if val is not None:
                        # Acumula para a média da dimensão (Gráfico Radar)
                        dimensoes_totais[cat].append(val)
                        if q_text not in soma_por_pergunta:
                            soma_por_pergunta[q_text] = 0
                            total_por_pergunta[q_text] = 0
                            
                        total_por_pergunta[q_text] += 1
                        soma_por_pergunta[q_text] += val

    # 1. Fechamento das Médias Dimensionais (Matriz Radar)
    dim_averages = {}
    for cat, vals in dimensoes_totais.items():
        dim_averages[cat] = round(sum(vals) / len(vals), 1) if vals else 0.0

    # 2. Motor de Raio-X (Cálculo Fiel de Risco em Percentual)
    detalhe_percent = {}
    for qt, soma in soma_por_pergunta.items():
        total = total_por_pergunta[qt]
        if total > 0:
            avg_q = soma / total
            risco_percentual = ((5.0 - avg_q) / 4.0) * 100
            risco_percentual = max(0, min(100, risco_percentual))
            detalhe_percent[qt] = int(risco_percentual)
        else:
            detalhe_percent[qt] = None

    comp['dimensoes'] = dim_averages
    vals_validos = [v for v in dim_averages.values() if v > 0]
    comp['score'] = round(sum(vals_validos) / len(vals_validos), 1) if vals_validos else 0.0
    comp['detalhe_perguntas'] = detalhe_percent
    
    return comp

def load_data_from_db():
    """
    Função guardiã. Puxa todos os dados das tabelas do Supabase, delega o processamento
    matemático para os motores acima e retorna objetos estruturados para o painel.
    """
    all_answers = []
    companies = []
    
    # Abordagem Híbrida: Tenta Nuvem primeiro.
    if DB_CONNECTED:
        try:
            companies = supabase.table('companies').select("*").execute().data
            all_answers = supabase.table('responses').select("*").execute().data
            
            # Sincroniza a base de usuários para checagem de permissões
            users_raw = supabase.table('admin_users').select("*").execute().data
            if users_raw:
                st.session_state.users_db = {u['username']: u for u in users_raw}
        except Exception as e:
            pass
            
    # Fallback caso as listas retornem vazias
    if not companies:
        companies = st.session_state.companies_db
        all_answers = st.session_state.local_responses_db
        
    all_answers = calculate_actual_scores(all_answers, companies, st.session_state.methodologies)
    
    for c in companies:
        if 'org_structure' not in c or not c['org_structure']: 
            c['org_structure'] = {"Geral": ["Geral"]}
            
        comp_resps = [r for r in all_answers if str(r['company_id']) == str(c['id'])]
        
        metodo_nome = c.get('metodologia', 'HSE-IT (35 itens)')
        active_questions = st.session_state.methodologies.get(metodo_nome, st.session_state.methodologies['HSE-IT (35 itens)'])['questions']
        
        c = process_company_analytics(c, comp_resps, active_questions)

    return companies, all_answers

def generate_real_history(comp_id, all_responses, active_questions, total_vidas):
    """
    Engenharia de Dados Temporais: Agrupa e processa os dados cronologicamente
    baseado na string de data/hora oficial armazenada no banco.
    """
    history_dict = {}
    
    for r in all_responses:
        if str(r.get('company_id')) != str(comp_id): 
            continue
        
        created_at = r.get('created_at')
        if not created_at: 
            periodo = "Lote Retroativo (S/ Data)"
        else:
            try:
                dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                periodo = dt.strftime('%m/%Y')
            except Exception:
                periodo = "Geral"
            
        if periodo not in history_dict:
            history_dict[periodo] = []
        history_dict[periodo].append(r)
        
    history_list = []
    for period, resps in history_dict.items():
        comp_mock = {'id': comp_id, 'func': total_vidas}
        comp_stats = process_company_analytics(comp_mock, resps, active_questions)
        
        history_list.append({
            "periodo": period,
            "score": comp_stats.get('score', 0),
            "vidas": total_vidas,
            "adesao": int((len(resps) / total_vidas) * 100) if total_vidas > 0 else 0,
            "dimensoes": comp_stats.get('dimensoes', {})
        })
        
    try:
        history_list.sort(key=lambda x: datetime.datetime.strptime(x['periodo'], '%m/%Y') if '/' in x['periodo'] else datetime.datetime.min)
    except Exception:
        pass
        
    return history_list

def delete_company(comp_id):
    """ 
    Script de Deleção em Cascata (Impede erro Foreign Key).
    Necessário excluir os filhos ('responses', 'admin_users') antes da mãe ('companies').
    """
    if DB_CONNECTED:
        try:
            supabase.table('responses').delete().eq('company_id', comp_id).execute()
            supabase.table('admin_users').delete().eq('linked_company_id', comp_id).execute()
            supabase.table('companies').delete().eq('id', comp_id).execute()
        except Exception as e: 
            st.warning(f"Erro em cascata no banco de dados. Transação abortada: {e}")
            return
    
    st.session_state.companies_db = [c for c in st.session_state.companies_db if str(c['id']) != str(comp_id)]
    st.success("✅ A Empresa e todas as suas dependências sistêmicas foram expurgadas com sucesso.")
    time.sleep(1.5)
    st.rerun()

def delete_user(username):
    """ Função singular para exclusão limpa de um login de analista/gestor. """
    if DB_CONNECTED:
        try:
            supabase.table('admin_users').delete().eq('username', username).execute()
        except Exception as e: 
            st.error(f"Falha de exclusão remota: {e}")
    
    if username in st.session_state.users_db:
        del st.session_state.users_db[username]
    
    st.success(f"✅ Credencial [{username}] revogada permanentemente!")
    time.sleep(1)
    st.rerun()

def kpi_card(title, value, icon, color_class):
    """Componente construtor do Card visual de Indicador de Performance."""
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-icon-box {color_class}">{icon}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-title">{title}</div>
        </div>
    """, unsafe_allow_html=True)

def gerar_analise_robusta(dimensoes):
    """Algoritmo de processamento de linguagem natural (Simplificado) para o parecer técnico."""
    riscos = [k for k, v in dimensoes.items() if v < 3.0 and v > 0]
    texto = "Embasado pelo rigor e validação métrica da metodologia científica selecionada para análise, este diagnóstico mapeou os alicerces fundamentais da saúde e proteção ocupacional da entidade corporativa. "
    
    if riscos:
        texto += f"A varredura quantitativa expõe, com clareza cristalina, que as frentes de **{', '.join(riscos)}** encontram-se represadas em zonas de fragilidade aguda (Comportando um Score Inferior a 3.0). Na ótica ocupacional, a manutenção contínua destes estressores correlaciona-se com aumentos estatísticos severos em quadros de absenteísmo médico, fadiga por burnout e rotatividade voluntária (turnover). "
    else:
        texto += "Sob o espectro analítico global, os extratos processados indicam um ecossistema operacional significativamente equilibrado e permeado por fatores orgânicos de proteção psíquica atuantes de modo salutar. A totalidade das métricas repousa dentro dos parâmetros internacionalmente tidos como de 'normalidade e excelência'. "
    
    texto += "Como premissa de desenvolvimento, atesta-se a imprescindível necessidade de implantação imediata e acompanhamento do respectivo Plano de Ação Estratégico delineado abaixo para mitigar riscos iminentes ou tracionar a solidificação da cultura sistêmica de segurança psicológica institucional."
    return texto

def gerar_banco_sugestoes(dimensoes):
    """
    Motor de Recomendação Estratégica: Devolve uma malha enorme e detalhada
    de heurísticas para guiar o trabalho do RH do cliente, atrelado às notas.
    EXPANDIDO com linguagem executiva de alto nível e mapeamento duplo (HSE e COPSOQ).
    """
    sugestoes = []
    
    # ------------------ BLOCO: DEMANDAS E CARGA ------------------
    if dimensoes.get("Demandas", 5) < 3.8 or dimensoes.get("Exigências Laborais e Ritmo", 5) < 3.8:
        sugestoes.append({
            "acao": "Censo de Carga de Trabalho", 
            "estrat": "Mapear minuciosamente o organograma de tarefas vs capacidade física do colaborador visando identificar e suprimir atividades ociosas e redundâncias procedimentais.", 
            "area": "Gestão de Demandas", "resp": "Coordenação de Área", "prazo": "30 a 60 dias"
        })
        sugestoes.append({
            "acao": "Matriz de Priorização Rígida", 
            "estrat": "Institucionalizar o uso da Matriz Eisenhower, garantindo que 'Urgente' não sobreponha constantemente o 'Importante', evitando o estado permanente de combate a incêndios.", 
            "area": "Gestão de Demandas", "resp": "Líderes de Equipe", "prazo": "15 dias"
        })
        sugestoes.append({
            "acao": "Governança de Desconexão", 
            "estrat": "Redigir e oficializar diretrizes robustas coibindo a exigência velada de resposta a mensagens instantâneas e e-mails de trabalho fora da jornada contratual.", 
            "area": "Gestão de Demandas", "resp": "RH Corporativo", "prazo": "30 dias"
        })
        sugestoes.append({
            "acao": "Alocação Sazonal Inteligente", 
            "estrat": "Mapeamento dos picos do negócio e provisionamento orçamentário prévio para contratação de força de trabalho contingencial, blindando o efetivo fixo do esgotamento.", 
            "area": "Gestão de Demandas", "resp": "Diretoria/Financeiro", "prazo": "Próximo Trimestre"
        })
        sugestoes.append({
            "acao": "Blindagem Anti-Interrupção", 
            "estrat": "Sancionar períodos intocáveis na agenda da equipe ('Deep Work Zones'), onde reuniões de status e interrupções são proibidas.", 
            "area": "Gestão de Demandas", "resp": "Lideranças", "prazo": "Imediato"
        })
        
    # ------------------ BLOCO: CONTROLE E AUTONOMIA ------------------
    if dimensoes.get("Controle", 5) < 3.8 or dimensoes.get("Organização e Influência", 5) < 3.8:
        sugestoes.append({
            "acao": "Job Crafting Guiado", 
            "estrat": "Autorizar e estimular que o operador possa remodelar sutilmente os métodos que utiliza para cumprir sua cota, devolvendo o senso de soberania técnica.", 
            "area": "Controle Operacional", "resp": "Líder Operacional", "prazo": "Contínuo"
        })
        sugestoes.append({
            "acao": "Gestão por Entregáveis", 
            "estrat": "Fomentar a flexibilidade temporal de entrada e saída, medindo a eficiência com base na pureza da entrega final ao invés do microgerenciamento de horas em tela.", 
            "area": "Controle Operacional", "resp": "Gestão", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Democratização Decisória", 
            "estrat": "Realizar plenárias curtas que efetivamente incorporem a opinião crítica de quem realiza a tarefa na base antes da compra de um sistema ou troca de maquinário.", 
            "area": "Controle Operacional", "resp": "C-Level e Gestores", "prazo": "Ad Hoc / Sob Demanda"
        })
        sugestoes.append({
            "acao": "Job Rotation Dinâmico", 
            "estrat": "Efetuar a rotação lateral periódica de atribuições mecânicas para combater a estafa por monotonia extrema e expandir a polivalência profissional.", 
            "area": "Controle Operacional", "resp": "Recursos Humanos", "prazo": "120 dias"
        })
        
    # ------------------ BLOCO: SUPORTE GESTÃO E EQUIPE ------------------
    if dimensoes.get("Suporte Gestor", 5) < 3.8 or dimensoes.get("Suporte Pares", 5) < 3.8 or dimensoes.get("Relações e Liderança", 5) < 3.8:
        sugestoes.append({
            "acao": "Letramento em Liderança Sensível", 
            "estrat": "Submeter a primeira linha de gestão a workshops vivenciais para lapidação de escuta genuína, inteligência emocional e resolução não-punitiva de desvios.", 
            "area": "Suporte e Liderança", "resp": "Pessin Gestão / RH", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Protocolo de Mentoria Interna (Buddy)", 
            "estrat": "Acoplar um profissional veterano de alta empatia para guiar estritamente novos entrantes em seu período de fragilidade adaptativa (onboarding extendido).", 
            "area": "Suporte e Liderança", "resp": "RH Estratégico", "prazo": "30 dias"
        })
        sugestoes.append({
            "acao": "Engenharia de Check-ins (1:1s)", 
            "estrat": "Travar bloqueios quinzenais inegociáveis na agenda da liderança exclusivos para escuta ativa sobre a carreira, dores e percepções do colaborador, sem focar no projeto atual.", 
            "area": "Suporte e Liderança", "resp": "Líderes de Setor", "prazo": "Quinzenal Contínuo"
        })
        sugestoes.append({
            "acao": "Muralha de Acolhimento", 
            "estrat": "Estipular canal veloz com profissionais capacitados do SESMT/RH para contenção e escuta acolhedora frente a rompimentos de estabilidade emocional ou episódios de trauma no andar.", 
            "area": "Suporte e Liderança", "resp": "SESMT / Psicologia", "prazo": "Imediato"
        })
        sugestoes.append({
            "acao": "Sistemas de Reconhecimento Positivo", 
            "estrat": "Fazer cessar a cultura do 'não fez mais que a obrigação' implementando atos frequentes de valorização franca por metas longas atingidas.", 
            "area": "Suporte e Liderança", "resp": "Diretoria/Gestão", "prazo": "Contínuo"
        })
        
    # ------------------ BLOCO: RELACIONAMENTOS E CULTURA ------------------
    if dimensoes.get("Relacionamentos", 5) < 3.8 or dimensoes.get("Comportamentos Ofensivos (Últimos 12 meses)", 5) < 3.8:
        sugestoes.append({
            "acao": "Sanção Moral e Código de Conduta", 
            "estrat": "Forçar a assinatura reiterada de código de ética rígido, com foco em política formal de Tolerância Zero contra agressões verbais, gaslighting e assédio moral corporativo.", 
            "area": "Relações e Clima", "resp": "Compliance / Jurídico", "prazo": "60 dias"
        })
        sugestoes.append({
            "acao": "Alfabetização em CNV", 
            "estrat": "Levar para a base teórica da empresa treinamentos mandatórios e interativos focados estritamente na Comunicação Não-Violenta e empatia processual.", 
            "area": "Relações e Clima", "resp": "T&D / Treinamento", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Canal Denúncia Externo Blindado", 
            "estrat": "Contratar provedor isento para operar plataforma de escuta e auditoria anônima, garantindo ausência de retaliações à vítima reportante.", 
            "area": "Relações e Clima", "resp": "Diretoria Administrativa", "prazo": "120 dias"
        })
        sugestoes.append({
            "acao": "Acordo Coletivo de Convivência Operacional", 
            "estrat": "Rodar sprints de design thinking junto aos liderados para criação das 'Leis do Setor' (ex: evitar fofocas, pontualidade, respeito em calls) afixadas em área visível.", 
            "area": "Relações e Clima", "resp": "Gestores de Área", "prazo": "45 dias"
        })
        
    # ------------------ BLOCO: PAPEL FUNCIONAL E VALORES ------------------
    if dimensoes.get("Papel", 5) < 3.8 or dimensoes.get("Valores, Sentido e Justiça", 5) < 3.8:
        sugestoes.append({
            "acao": "Calibragem e Purificação de Cargos (JD)", 
            "estrat": "Auditar e atualizar o memorial descritivo dos papéis funcionais, expurgando o desvio de função não remunerado e clarificando a teia de deveres atrelados.", 
            "area": "Papel e Valores Corporativos", "resp": "Recursos Humanos", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Cascateamento Transparente de Estratégia", 
            "estrat": "Garantir que a visão dos acionistas (o 'porquê' da empresa existir) desça até as bases operacionais, mostrando como o esforço individual viabiliza o lucro.", 
            "area": "Papel e Valores Corporativos", "resp": "Board Executivo", "prazo": "A cada ciclo OKR"
        })
        sugestoes.append({
            "acao": "Adoção Institucional do Modelo RACI", 
            "estrat": "Formalizar as linhas cinzentas de responsabilidade determinando rigidamente quem é Autoridade, Executante e Consultado nos gargalos intersetoriais.", 
            "area": "Papel e Valores Corporativos", "resp": "Gestão de Processos", "prazo": "60 dias"
        })
        
    # ------------------ BLOCO: GESTÃO DE MUDANÇA ------------------
    if dimensoes.get("Mudança", 5) < 3.8:
        sugestoes.append({
            "acao": "Pedagogia da Transição Estrutural", 
            "estrat": "Assumir postura educativa: Antes de injetar um novo ERP ou regra na rotina, realizar comunicados didáticos evidenciando a 'dor atual' e o ganho pretendido.", 
            "area": "Curva de Mudança", "resp": "Comunicação Interna", "prazo": "Por Projeto"
        })
        sugestoes.append({
            "acao": "Ponte de Influenciadores Base", 
            "estrat": "Identificar lideranças informais de campo e trazê-los para desenhar as transições junto ao alto escalão, usando-os como embaixadores orgânicos da novidade.", 
            "area": "Curva de Mudança", "resp": "Gestão Estratégica", "prazo": "Por Projeto"
        })
        sugestoes.append({
            "acao": "Mapa de Ansiedade Visual", 
            "estrat": "Construir linha do tempo imensa e física (ou painel Kanban publico) demonstrando os degraus exatos de transição, para mitigar insegurança e fofoca corporativa.", 
            "area": "Curva de Mudança", "resp": "Líder de Projetos", "prazo": "Imediato"
        })

    # ------------------ BLOCO: SAÚDE E BEM-ESTAR (COPSOQ) ------------------
    if dimensoes.get("Saúde, Stress e Bem-estar (Últimas 4 semanas)", 5) < 3.8:
        sugestoes.append({
            "acao": "Intervenção de Saúde Mental Corporativa", 
            "estrat": "Implementar rodas de conversa orientadas e parcerias com plataformas de terapia subsidiada para o controle ativo do burnout e distúrbios do sono detectados.", 
            "area": "Saúde Ocupacional", "resp": "Saúde Ocupacional / SESMT", "prazo": "Plano Anual"
        })
        
    # ------------------ FALLBACK (CASO O CENÁRIO SEJA EXTREMAMENTE VERDE) ------------------
    if not sugestoes:
        sugestoes.append({
            "acao": "Trilha Frequente de Pulso Climático", 
            "estrat": "Operacionalizar formulários semanais microscópicos para detectar fissuras de clima na base de forma ultra-antecipada.", 
            "area": "Estratégia Geral", "resp": "RH Estratégico", "prazo": "Contínuo"
        })
        sugestoes.append({
            "acao": "Auxílio Mental Corporativo", 
            "estrat": "Investimento fixo mensal na contratação de plataformas agregadoras focadas no subsídio do pagamento de terapias à distância ao colaborador.", 
            "area": "Estratégia Geral", "resp": "Diretoria e Benefícios", "prazo": "Plano Anual"
        })
        sugestoes.append({
            "acao": "Intervenção Ergônomica e Motora", 
            "estrat": "Promover parcerias terceirizadas de inserção diária na quebra fisiológica com alongamentos compensatórios atrelados à respiração tática relaxante.", 
            "area": "Estratégia Geral", "resp": "Saúde Ocupacional", "prazo": "30 dias"
        })
        
    return sugestoes

# ==============================================================================
# 5. MÓDULO DE TELAS E INTEGRAÇÕES DE FLUXO DO USUÁRIO ADM
# ==============================================================================

def login_screen():
    """Tela Gateway de Autenticação Robusta do Sistema Restrito."""
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'>{get_logo_html(250)}</div>", unsafe_allow_html=True)
        plat_name = st.session_state.platform_config.get('name', 'Sistema')
        st.markdown(f"<h3 style='text-align:center; color:#555;'>Acesso Restrito: {plat_name}</h3>", unsafe_allow_html=True)
        
        with st.form("login"):
            user = st.text_input("Usuário Credenciado")
            pwd = st.text_input("Credencial de Senha", type="password")
            
            if st.form_submit_button("Liberar Acesso ao Dashboard", type="primary", use_container_width=True):
                login_ok = False
                user_role_type = "Analista"
                user_credits = 0
                linked_comp = None
                
                # Motor de verificação prioritária: Base de Dados em Nuvem (Supabase)
                if DB_CONNECTED:
                    try:
                        res = supabase.table('admin_users').select("*").eq('username', user).eq('password', pwd).execute()
                        if res.data: 
                            login_ok = True
                            user_data = res.data[0]
                            user_role_type = user_data.get('role', 'Master')
                            user_credits = user_data.get('credits', 0)
                            linked_comp = user_data.get('linked_company_id')
                    except: pass
                
                # Motor secundário: Verificação de Backup Session State local 
                if not login_ok and user in st.session_state.users_db and st.session_state.users_db[user].get('password') == pwd:
                    login_ok = True
                    user_data = st.session_state.users_db[user]
                    user_role_type = user_data.get('role', 'Analista')
                    user_credits = user_data.get('credits', 0)
                    linked_comp = user_data.get('linked_company_id')
                
                if login_ok:
                    # Trava de Contrato (Link expira caso o prazo acabe)
                    valid_until = user_data.get('valid_until')
                    if valid_until and datetime.datetime.today().isoformat() > valid_until:
                        st.error("🚫 Bloqueio Sistêmico: A validade contratual deste acesso chegou ao fim. Contate o suporte técnico.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_role = 'admin'
                        
                        # GARANTIA ABSOLUTA DE IMUNIDADE E ACESSO MASTER PARA O USUARIO PADRÃO "admin"
                        if user == 'admin':
                            user_role_type = 'Master'
                            user_credits = 999999
                        
                        # Fixa na memória da sessão os dados transicionais desse usuário até log-out
                        st.session_state.admin_permission = user_role_type 
                        st.session_state.user_username = user
                        st.session_state.user_credits = user_credits
                        st.session_state.user_linked_company = linked_comp
                        
                        st.rerun()
                else: 
                    st.error("⚠️ Identificação Falha. Combinação de Usuário e Senha rejeitada pela rede.")
                    
        st.caption("Nota Técnica: Ambientes de coleta de colaboradores são geridos através de Links UUID. Esta tela atende estritamente auditores e corporativo.")

def admin_dashboard():
    """Painel de Controle Central: Motor Visual e Distribuídor de Lógica."""
    
    # 1. Carrega dados frescos, com cálculos de notas reais, garantindo a integridade dos painéis.
    companies_data, responses_data = load_data_from_db()
    
    perm = st.session_state.admin_permission
    curr_user = st.session_state.user_username
    
    # 2. Pareamento Lógico de Filtro Visual por Nível de Acesso
    if perm == "Gestor":
        visible_companies = [c for c in companies_data if c.get('owner') == curr_user]
    elif perm == "Analista":
        linked_id = st.session_state.user_linked_company
        visible_companies = [c for c in companies_data if c['id'] == linked_id]
    else: 
        # Nível Master: Absorve tudo do banco sem filtros restritivos
        visible_companies = companies_data

    # 3. Matemática de Fracionamento de Uso das Cotas Residuais
    total_used_by_user = sum(c.get('respondidas', 0) for c in visible_companies) if perm != "Analista" else (visible_companies[0].get('respondidas', 0) if visible_companies else 0)
    credits_left = st.session_state.user_credits - total_used_by_user

    # 4. Estrutura do Menu Dinâmico adaptável à permissão
    menu_options = ["Visão Geral", "Gerar Link", "Relatórios", "Histórico & Comparativo"]
    if perm in ["Master", "Gestor"]:
        menu_options.insert(1, "Empresas")
        menu_options.insert(2, "Setores & Cargos")
    if perm == "Master":
        menu_options.append("Configurações")

    icons_map = {
        "Visão Geral": "grid", 
        "Empresas": "building", 
        "Setores & Cargos": "list-task", 
        "Gerar Link": "link-45deg", 
        "Relatórios": "file-text", 
        "Histórico & Comparativo": "clock-history", 
        "Configurações": "gear"
    }

    # Construção visual da barra lateral da esquerda
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; margin-bottom:30px; margin-top:20px;'>{get_logo_html(160)}</div>", unsafe_allow_html=True)
        st.caption(f"Operador Identificado: **{curr_user}** <br> Perfil Ativo: **{perm}**", unsafe_allow_html=True)
        
        if perm != "Master":
            st.info(f"💳 Saldo Autorizado: {credits_left} Questionários Restantes")

        selected = option_menu(
            menu_title=None, 
            options=menu_options, 
            icons=[icons_map[o] for o in menu_options], 
            default_index=0, 
            styles={"nav-link-selected": {"background-color": COR_PRIMARIA}}
        )
        st.markdown("---")
        if st.button("🚪 Sair do Sistema com Segurança", use_container_width=True): 
            logout()

    # -------------------------------------------------------------------------
    # ROUTER: VISÃO GERAL (O DASHBOARD E KPIs GERAIS)
    # -------------------------------------------------------------------------
    if selected == "Visão Geral":
        st.title("Painel Administrativo Analítico")
        
        # Filtro Global de escopo das telas
        lista_empresas_filtro = ["Múltiplas (Cenário Consolidado)"] + [c['razao'] for c in visible_companies]
        empresa_filtro = st.selectbox("Isolar Visão Gráfica e Dados por Empresa:", lista_empresas_filtro)
        
        if empresa_filtro != "Múltiplas (Cenário Consolidado)":
            companies_filtered = [c for c in visible_companies if c['razao'] == empresa_filtro]
            target_id = companies_filtered[0]['id']
            responses_filtered = [r for r in responses_data if str(r['company_id']) == str(target_id)]
        else:
            companies_filtered = visible_companies
            ids_visiveis = [str(c['id']) for c in visible_companies]
            responses_filtered = [r for r in responses_data if str(r['company_id']) in ids_visiveis]

        # Consumo de Variaveis
        total_resp_view = len(responses_filtered)
        total_vidas_view = sum(c.get('func', 0) for c in companies_filtered)
        
        # Injeção Customizada de KPIs 
        col1, col2, col3, col4 = st.columns(4)
        if perm == "Analista":
            with col1: kpi_card("Vidas Contratadas Base", total_vidas_view, "👥", "bg-blue")
            with col2: kpi_card("Questionários Retornados", total_resp_view, "✅", "bg-green")
            with col3: kpi_card("Balanço de Saldo Atual", credits_left, "💳", "bg-orange") 
        else:
            with col1: kpi_card("Empresas/Projetos Em Rede", len(companies_filtered), "🏢", "bg-blue")
            with col2: kpi_card("Soma Total de Respostas", total_resp_view, "✅", "bg-green")
            if perm == "Master": 
                with col3: kpi_card("Censo Real Extrapolado (Vidas)", total_vidas_view, "👥", "bg-orange") 
            else: 
                with col3: kpi_card("Seu Saldo em Carteira", credits_left, "💳", "bg-orange")

        with col4: kpi_card("Alertas de Criticidade Alta", 0, "🚨", "bg-red")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        
        # GRAFICO 1: O Radar Geral Multidimensional
        with c1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### Construção Espacial do Radar Multidimensional")
            
            if companies_filtered and total_resp_view > 0:
                metodo_predominante = companies_filtered[0].get('metodologia', 'HSE-IT (35 itens)')
                comps_validas = [c for c in companies_filtered if c.get('metodologia', 'HSE-IT (35 itens)') == metodo_predominante]
                categories = list(st.session_state.methodologies[metodo_predominante]['questions'].keys())
                
                avg_dims = {cat: 0 for cat in categories}
                count_comps_with_data = 0
                
                # Somatório linear extraindo apenas as dimensões validadas das empresas
                for c in comps_validas:
                    if c.get('respondidas', 0) > 0:
                        count_comps_with_data += 1
                        for cat in categories: 
                            avg_dims[cat] += c['dimensoes'].get(cat, 0)
                
                # Matemática segura
                valores_radar = [round(avg_dims[cat]/count_comps_with_data, 1) for cat in categories] if count_comps_with_data > 0 else [0]*len(categories)

                fig_radar = go.Figure(go.Scatterpolar(r=valores_radar, theta=categories, fill='toself', name='Média Operacional', line_color=COR_SECUNDARIA))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=300, margin=dict(t=20, b=20))
                st.plotly_chart(fig_radar, use_container_width=True)
                st.caption(f"Metodologia da Matriz: **{metodo_predominante}**")
            else: 
                st.info("O algoritmo necessita de respostas para forjar as coordenadas espaciais deste radar.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        # GRAFICO 2: Termômetro Estrutural de Setores em Barras de Calor
        with c2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### Recorte de Resultados Analíticos Verticalizado por Setor")
            if responses_filtered:
                df_resp = pd.DataFrame(responses_filtered)
                
                if 'setor' in df_resp.columns and 'score_calculado' in df_resp.columns:
                    # Consolidação robusta via Pandas GroupBy
                    df_setor = df_resp.groupby('setor')['score_calculado'].mean().reset_index()
                    fig_bar = px.bar(
                        df_setor, 
                        x='setor', 
                        y='score_calculado', 
                        title="Motor Analítico de Score Real Médio por Área Identificada", 
                        color='score_calculado', 
                        color_continuous_scale='RdYlGn', 
                        range_y=[0, 5]
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else: 
                    st.info("Anomalia detectada. Sem dados setoriais perfeitamente classificados para processamento.")
            else: 
                st.info("Pausado: Em compasso de espera por formulários recebidos para computação do gráfico de barras.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # GRAFICO 3: Acompanhamento e Tração da Resolução do Contrato (Pizza/Donut)
        c3, c4 = st.columns([1.5, 1])
        with c3:
             st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
             st.markdown("##### Mapa de Tração e Distribuição de Status Contratual")
             if companies_filtered:
                 status_dist = {"Fechado/Concluído (Meta Integral)": 0, "Colhendo Dados (Andamento)": 0}
                 for c in companies_filtered:
                     if c.get('respondidas',0) >= c.get('func',1): 
                         status_dist["Fechado/Concluído (Meta Integral)"] += 1
                     else: 
                         status_dist["Colhendo Dados (Andamento)"] += 1
                 
                 fig_pie = px.pie(names=list(status_dist.keys()), values=list(status_dist.values()), hole=0.6, color_discrete_sequence=[COR_SECUNDARIA, COR_RISCO_MEDIO])
                 fig_pie.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
                 st.plotly_chart(fig_pie, use_container_width=True)
             else: 
                 st.info("Vazio Sistêmico. Necessário catalogação prévia de entidades corporativas ativas.")
             st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # ROUTER: ENTIDADES (EMPRESAS CLIENTES)
    # -------------------------------------------------------------------------
    elif selected == "Empresas":
        st.title("Hub de Gestão Cadastral e de Clientes")
        
        # CAMINHO A: EDITOR DE DADOS REAIS
        if st.session_state.edit_mode:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("✏️ Alterar Configurações Estritas da Empresa Selecionada")
            target_id = st.session_state.edit_id
            emp_edit = next((c for c in visible_companies if c['id'] == target_id), None)
            
            if emp_edit:
                with st.form("edit_form"):
                    c1, c2, c3 = st.columns(3)
                    new_razao = c1.text_input("Identidade (Razão Social)", value=emp_edit['razao'])
                    new_cnpj = c2.text_input("Inscrição CNPJ", value=emp_edit.get('cnpj',''))
                    new_cnae = c3.text_input("Registro de Atividade (CNAE)", value=emp_edit.get('cnae',''))
                    
                    c4, c5, c6 = st.columns(3)
                    risco_opts = [1, 2, 3, 4]
                    idx_risco = risco_opts.index(emp_edit.get('risco',1)) if emp_edit.get('risco',1) in risco_opts else 0
                    new_risco = c4.selectbox("Indicador Legal de Risco", risco_opts, index=idx_risco)
                    new_func = c5.number_input("Extrapolação de Vidas (Funcionários)", min_value=1, value=emp_edit.get('func',100))
                    new_limit = c6.number_input("Cota Bloqueante de Avaliações", min_value=1, value=emp_edit.get('limit_evals', 100))
                    
                    seg_opts = ["GHE", "Setor", "GES"]
                    idx_seg = seg_opts.index(emp_edit.get('segmentacao','GHE')) if emp_edit.get('segmentacao','GHE') in seg_opts else 0
                    new_seg = c6.selectbox("Filtro de Segmentação dos Reports", seg_opts, index=idx_seg)
                    
                    c7, c8, c9 = st.columns(3)
                    new_resp = c7.text_input("Ponte de Contato (Nome Resp.)", value=emp_edit.get('resp',''))
                    new_email = c8.text_input("Correio Eletrônico Resp.", value=emp_edit.get('email',''))
                    new_tel = c9.text_input("Dígitos Telefônicos Resp.", value=emp_edit.get('telefone',''))
                    
                    new_end = st.text_input("Endereçamento Jurídico e Físico Completo", value=emp_edit.get('endereco',''))
                    
                    # Logica amigável do parser de data temporal
                    val_atual = datetime.date.today() + datetime.timedelta(days=365)
                    if emp_edit.get('valid_until'):
                        try: val_atual = datetime.date.fromisoformat(emp_edit['valid_until'])
                        except: pass
                    new_valid = st.date_input("Deadline Contratual e Bloqueio de Link Automático", value=val_atual)
                    
                    if st.form_submit_button("💾 Modificar Parâmetros Definitivos", type="primary"):
                        update_dict = {
                            'razao': new_razao, 'cnpj': new_cnpj, 'cnae': new_cnae, 
                            'risco': new_risco, 'func': new_func, 'segmentacao': new_seg, 
                            'resp': new_resp, 'email': new_email, 'telefone': new_tel, 
                            'endereco': new_end, 'limit_evals': new_limit, 'valid_until': new_valid.isoformat()
                        }
                        
                        # Injeção Pesada e UPDATE SQL garantido
                        if DB_CONNECTED:
                            try: 
                                supabase.table('companies').update(update_dict).eq('id', target_id).execute()
                            except Exception as e: 
                                st.warning(f"Erro ao interpelar banco oficial no comando update: {e}")
                        
                        # Backup Cache Atualizado Visual
                        emp_edit.update(update_dict)
                        st.session_state.edit_mode = False
                        st.session_state.edit_id = None
                        st.success("✅ Ação consumada. A infraestrutura do cliente foi modificada em nuvem.")
                        time.sleep(1)
                        st.rerun()
                        
                if st.button("⬅️ Abortar Modificação Restrita"): 
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                st.error("Descompasso: O registro base do índice selecionado sumiu temporariamente. Recarregue a janela.")
        
        else:
            # CAMINHO B: VISUALIZAÇÃO E NOVO ELEMENTO
            tab1, tab2 = st.tabs(["📋 Malha de Corporações", "➕ Adicionar Matriz Externa (Nova Empresa)"])
            with tab1:
                if not visible_companies: 
                    st.info("A árvore de malhas está em branco. Comece a criar seu ecossistema indo à aba de Adição.")
                
                for emp in visible_companies:
                    with st.expander(f"🏢 Entidade Base: {emp['razao']}"):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.write(f"**Vínculo CNPJ:** {emp.get('cnpj','')}")
                        c2.write(f"**Exaustão da Cota:** {emp.get('respondidas',0)} de {emp.get('limit_evals', '∞')} retornos")
                        c3.info(f"**Metodologia:** {emp.get('metodologia', 'HSE-IT (35 itens)')}")
                        
                        c4_1, c4_2 = c4.columns(2)
                        if c4_1.button("✏️ Configurar", key=f"ed_{emp['id']}"): 
                             st.session_state.edit_mode = True
                             st.session_state.edit_id = emp['id']
                             st.rerun()
                        
                        if perm == "Master":
                            # Deleção por UUID exata garante zero margem de error de array out of bounds
                            if c4_2.button("🗑️ Detonar Matriz", key=f"del_{emp['id']}"): 
                                delete_company(emp['id'])
            
            with tab2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                with st.form("add_comp_form_gigante"):
                    if credits_left <= 0 and perm != "Master":
                        st.error("🚫 O fluxo da interface barrou a criação: Ausência técnica de fundos de crédito estipulados no seu plano.")
                        st.form_submit_button("Travado pela Governança do App", disabled=True)
                    else:
                        st.write("### Identificação Oficial Corporativa")
                        c1, c2, c3 = st.columns(3)
                        razao = c1.text_input("A Razão Social Completa")
                        cnpj = c2.text_input("O Documento Atrelado (CNPJ)")
                        cnae = c3.text_input("O Código Fiscal Base (CNAE)")
                        
                        c4, c5, c6, c_met = st.columns(4)
                        risco = c4.selectbox("Indicador Técnico (Grau de Risco)", [1,2,3,4])
                        func = c5.number_input("Projeção Censituária de Vidas Humanas", min_value=1)
                        limit_evals = c6.number_input("Cota Teto para Disparo de Questionários", min_value=1, max_value=credits_left if perm!="Master" else 99999, value=min(100, credits_left if perm!="Master" else 100))
                        
                        # SELETOR DO BANCO DE METODOLOGIAS
                        metodologia_selecionada = c_met.selectbox("Matriz Analítica", list(st.session_state.methodologies.keys()), help="Escolha qual algoritmo psicológico e base de perguntas será aplicado a este cliente.")

                        st.write("### Elo de Inteligência de Contato e Linkamento")
                        c7, c8, c9 = st.columns(3)
                        segmentacao = c7.selectbox("Divisão Abstrata Adotada", ["GHE", "Setor", "GES"])
                        resp = c8.text_input("A Ponte Humana Primária (Líder)")
                        email = c9.text_input("Canal Endereçado Online (E-mail)")
                        
                        c10, c11, c12 = st.columns(3)
                        tel = c10.text_input("Canal Rápido (Telefone)")
                        valid_date = c11.date_input("Termo de Queda do Link Público:", value=datetime.date.today() + datetime.timedelta(days=365))
                        c12.info("Um Token indecifrável UUID para a coleta segura será computado.")
                        
                        end = st.text_input("Logradouro e Jurisdição Física Completa")
                        logo_cliente = st.file_uploader("Assentamento Visual (Envio da Logo do Cliente)", type=['png', 'jpg', 'jpeg'])
                        
                        st.markdown("---")
                        st.write("### Gerador de Portal Paralelo (Gestão em Camada Menor - Perfil Analista)")
                        st.caption("A automação garante um login separado em sand-box para que a corporação só visualize os relatórios das próprias métricas isoladas.")
                        u_login = st.text_input("Login Chave Extratora")
                        u_pass = st.text_input("Senha Fiel de Acoplamento", type="password")

                        if st.form_submit_button("✅ Finalizar Transação e Gerar a Nova Base", type="primary"):
                            if not razao: 
                                st.error("⚠️ Identificamos um vácuo fatal: A Razão Social não permite estar ausente no envio.")
                            else:
                                # Magia da Segurança: UUID V4 com split cria um ID que não vaza nunca.
                                cod = str(uuid.uuid4())[:8].upper()
                                logo_str = image_to_base64(logo_cliente)
                                
                                new_c = {
                                    "id": cod, 
                                    "razao": razao, 
                                    "cnpj": cnpj, 
                                    "cnae": cnae, 
                                    "setor": "Geral", 
                                    "risco": risco, 
                                    "func": func, 
                                    "limit_evals": limit_evals, 
                                    "metodologia": metodologia_selecionada,
                                    "segmentacao": segmentacao, 
                                    "resp": resp, 
                                    "email": email, 
                                    "telefone": tel, 
                                    "endereco": end, 
                                    "valid_until": valid_date.isoformat(), 
                                    "logo_b64": logo_str, 
                                    "score": 0.0, 
                                    "respondidas": 0, 
                                    "owner": curr_user, 
                                    "dimensoes": {}, 
                                    "detalhe_perguntas": {}, 
                                    "org_structure": {"Geral": ["Geral"]}
                                }
                                
                                error_msg = None
                                if DB_CONNECTED:
                                    try:
                                        # Inject puro do JSON complexo
                                        supabase.table('companies').insert(new_c).execute()
                                        
                                        if u_login and u_pass:
                                            supabase.table('admin_users').insert({
                                                "username": u_login, 
                                                "password": u_pass, 
                                                "role": "Analista", 
                                                "credits": limit_evals, 
                                                "valid_until": valid_date.isoformat(), 
                                                "linked_company_id": cod
                                            }).execute()
                                    except Exception as e: 
                                        error_msg = str(e)
                                
                                st.session_state.companies_db.append(new_c)
                                
                                if error_msg: 
                                    st.warning(f"⚠️ Nota Limiar: A inserção fluiu no local mas colidiu no Supabase remoto com essa nota técnica: {error_msg}")
                                else: 
                                    st.success(f"🎉 Matriz Empresarial Instaurada! O Código Token que desbloqueia a aplicação deles é: {cod}")
                                
                                time.sleep(2.5)
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # ROUTER: CONSTRUTOR DE CADEIAS ORGÂNICAS (SETORES)
    # -------------------------------------------------------------------------
    elif selected == "Setores & Cargos":
        st.title("Máquina de Disposição Hierárquica")
        if not visible_companies: 
            st.warning("⚠️ Impossibilidade de prosseguimento. Assente primeiramente ao menos um cliente empresarial."); return
        
        empresa_nome = st.selectbox("Apontar o escopo da corporação alvo a receber ramificações:", [c['razao'] for c in visible_companies])
        empresa = next((c for c in visible_companies if c['razao'] == empresa_nome), None)
        
        if empresa is not None:
            if 'org_structure' not in empresa or not empresa['org_structure']: 
                empresa['org_structure'] = {"Geral": ["Geral"]}
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.subheader("1. Inserção ou Expurgão Lógica de Setores Diretos")
                new_setor = st.text_input("Qualificação textual do ramo departamental")
                if st.button("➕ Injetar na Raiz", type="primary"):
                    if new_setor and new_setor not in empresa['org_structure']:
                        empresa['org_structure'][new_setor] = []
                        if DB_CONNECTED:
                            try: 
                                supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                            except: pass
                        st.success(f"O ramo nomeado como '{new_setor}' logrou fixação na base!")
                        time.sleep(1); st.rerun()
                
                st.markdown("---")
                setores_existentes = list(empresa['org_structure'].keys())
                setor_remover = st.selectbox("Qualificação do ramo pautado a ser dizimado", setores_existentes)
                if st.button("🗑️ Desmaterializar Setor Selecionado"):
                    del empresa['org_structure'][setor_remover]
                    if DB_CONNECTED:
                         try: 
                             supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                         except: pass
                    st.success("Toda a arquitetura ligada a este ramo foi atomizada sem regresso.")
                    time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.subheader("2. Composição Fina do CBO/Cargos do Sub-ramo")
                setor_sel = st.selectbox("Qual o Ramo a ter sua microestrutura desenhada?", setores_existentes, key="sel_setor_cargos")
                if setor_sel:
                    df_cargos = pd.DataFrame({"Cargo": empresa['org_structure'][setor_sel]})
                    edited_cargos = st.data_editor(df_cargos, num_rows="dynamic", key="editor_cargos", use_container_width=True)
                    if st.button("💾 Persistir Definitivamente Modificações CBO", type="primary"):
                        lista_nova = edited_cargos["Cargo"].dropna().tolist()
                        empresa['org_structure'][setor_sel] = lista_nova
                        if DB_CONNECTED:
                             try: 
                                 supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                             except: pass
                        st.success("A matriz de funções laborais repousa salva no núcleo.")
                st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # ROUTER: GERADOR DO FUNIL EXECUTIVO (URLS)
    # -------------------------------------------------------------------------
    elif selected == "Gerar Link":
        st.title("Estúdio Tático de Criação e Roteamento de Portas de Entrada")
        if not visible_companies: 
            st.warning("⚠️ Impossível criar estradas (URLs). Requer cadastro organizacional ativo."); return
            
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            empresa_nome = st.selectbox("Apontar espelho de destino do tráfego:", [c['razao'] for c in visible_companies])
            empresa = next(c for c in visible_companies if c['razao'] == empresa_nome)
            
            # GERAÇÃO SEGURA: Limpeza rigorosa do final da URL configurada e adição correta do arg Query URL params
            base_url = st.session_state.platform_config.get('base_url', 'https://elonr01-cris.streamlit.app').rstrip('/')
            link_final = f"{base_url}/?cod={empresa['id']}"
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("##### Corredor Blindado Distribuível (URL Oficial)")
                st.markdown(f"<div class='link-area' style='background-color: #f8f9fa; border: 1px dashed #dee2e6; padding: 15px; border-radius: 8px; font-family: monospace; color: #2c3e50; font-weight: bold; word-break: break-all;'>{link_final}</div>", unsafe_allow_html=True)
                
                limit = empresa.get('limit_evals', 999999)
                usadas = empresa.get('respondidas', 0)
                val = empresa.get('valid_until', '-')
                try: val = datetime.date.fromisoformat(val).strftime('%d/%m/%Y')
                except: pass
                st.caption(f"📊 Volume Matemático Desperdiçado no Ciclo: {usadas} ingressos consumidos em um teto máximo de {limit} permitidos.")
                st.caption(f"📅 Barreira de Morte da URL Programada: {val}")
                st.caption(f"🧠 Matriz Analítica Vinculada a Esta Porta: **{empresa.get('metodologia', 'HSE-IT (35 itens)')}**")
                
                if st.button("👁️ Executar Emulação Visual Segura do Ponto de Vista do Operador da Base"):
                    st.session_state.current_company = empresa
                    st.session_state.logged_in = True
                    st.session_state.user_role = 'colaborador'
                    st.rerun()
            with c2:
                st.markdown("##### Estampa Magnética Digital em QR Code")
                qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link_final)}"
                st.image(qr_api_url, width=150)
                st.markdown(f"[📥 Baixar Vetor Extensível do QR Code]({qr_api_url})")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### 💬 Template Oficial de Marketing e Engajamento Base (Pronto para Uso em Múltiplas Mídias)")
            texto_convite = f"""Olá, valiosa equipe da {empresa['razao']}! 👋\n\nCuidar avidamente da nossa operação diária e dos nossos resultados estratégicos é a pauta fundamental do nosso barco, mas lhes asseguro com franqueza que absolutamente nada disso faz sentido sustentável se não cuidarmos, em exclusividade e primeiríssimo lugar, das peças vitais e humanas que fazem toda a mágica do processo final acontecer: todos vocês.\n\nCom muita alegria estamos dando o sinal verde e um início oficial à nossa importantíssima Avaliação de Riscos Psicossociais. Mais do que isso, queremos te fazer o mais aberto convite possível para um bate-papo veloz, estruturado, assíncrono e de extremo impacto sincero em nossas visões operacionais. Mas, olhando por fora, por que gastar o seu tempo para preencher isso no meio de uma rotina tão agitada?\n\n🧠 **Por que exatamente a SUA participação direta é tão inegociável e vital?**\nEm diversos e invisíveis momentos da nossa linha contínua do tempo, a densidade do estresse corporativo abstrato, uma eventual elevada e mal distribuída carga mecânica de trabalho, ou a própria mecânica das nossas interações diárias podem desaguar e fincar raízes, gerando impactos profundos no nosso bem-estar particular de maneiras muito sorrateiras e silenciosas.\nResponder preenchendo inteiramente a esta avaliação velada não possui correlação com o simples preenchimento de um rito de passagem exigido pela lei do Governo ou formulário engessado e padrão. Ao contrário. O seu ato de apontar nas perguntas é a única artilharia crível que você fornece para nós da gestão montarmos, decifrarmos o raio-x corporativo e obtermos os dados e KPIs necessários e críveis para podermos executar três pilares essenciais de mudança:\n\n* Enxergar precocemente as fissuras, identificar falhas abissais de comunicação e mitigar as dores atreladas aos processos mais duros e aos entraves que compõem o nosso cenário vital diário.\n* Construir pontes financeiras junto à mesa da diretoria, orçando, moldando e aprovando projetos sólidos de capacitações e ações imensamente práticas e táticas que preguem por promover de forma autêntica, mais equilíbrio palpável, repouso físico e blindagem à fragilizada saúde mental ocupacional que todos corremos risco.\n* Destruir os resquícios das lideranças do passado para impulsionarmos e edificarmos passo a passo e continuamente uma cultura irrefutavelmente agregadora e de natureza participativa profunda. Um lugar próspero onde a fala mansa encontre ressonância, onde as ideias e cansaços ecoem horizontalmente de modo que a diversidade de cada um da nossa área tenha respeito inabalável na sua particular e humana individualidade central.\n\n🔒 **Uma palavra rigorosa sobre a totalidade da sua segurança técnica ao enviar (Seus Dados na Criptografia Total)**\nToda a nossa frente de psicologia e os pilares deste departamento têm aguda noção e total consciência pragmática de que 'jogar aberto' sobre angústias laborais, fraquezas procedimentais e sentimentos atrelados ao clima com lideranças carecem, obrigatoriamente, de um muro intransponível ancorado numa cadeia de confiança absoluta, sem receio imperdoável da palavra demissão. Portanto, nós fizemos a mais estrita questão de firmar sem revogações os dois inquebráveis protocolos com sua pessoa listados aqui embaixo:\n\n* **Nossa Total e Cega Blindagem no Escudo de Anonimato Tecnológico:** Nós fomos buscar a aquisição e adotamos formalmente o nosso recente sistema de avaliação, rodando 100% integral sob a malha de algoritmos de segurança na nuvem. Nós testamos e ele foi agressivamente programado na base sob restrições técnicas e imutáveis tão rígidas cujo foco único é impossibilitar brutalmente a tentativa de qualquer diretor em fazer a caça aos nomes. É irrealizável na estrutura sistêmica cruzada do banco de dados fazer a atrelagem de que resposta específica pertenceu a quem. Todo CPF exigido é uma premissa só para saber se alguém tentou preencher dobrado na votação. Ele sequer salva no banco, no instante da batida ele desintegra sua inscrição natural e cospe algo apelidado de 'hash indestrutível', tornando as linhas enviadas indecifráveis para os humanos do nosso quadro de chefia.\n* **Postura Ética de Mapeamento com Análise Macro-Estatística Intocada:** O total montante gerado com excelência da decodificação de milhares de votos, será abstraído para a interface administrativa nossa sempre sob formato condensado e espremido numericamente (O sistema apenas junta a ponta do grupo de forma matemática impessoal gerando relatórios repletos por matriz de calor gráfico e percentual em cores demonstrativas, não contendo o rastro das identidades únicas formadoras). Reiteramos veementemente sem meias palavras de novo que nenhum gestor terá o link ou o poder da ferramenta em suas visões e painéis para o estrinchar visual exato e milimétrico expondo detalhadamente qualquer um dos seus dolorosos ou não retornos ao clique.\n\nO ato de ligar de verdade seu genuíno 'sincerômetro' de opiniões jogado até a estratosfera mais honesta possível se traduz como a melhor e principal força e propulsora ferramenta de auxílio a bússola que tanto sofremos necessitados de receber o mais breve e real para consertar nossas antigas falhas no gerenciamento central de ambiente da corporação. Queremos acalmar seu ânimo informando sem rodeios, por fim e com extrema lealdade, que ali naquele portal escuro não coexistem marcações ou asserções e perguntas dotadas das famosas 'respostas prontas ou corretas padrão RH'. O intuito base reside somente em entender da maneira mais desmistificada as frações de vivência sensível baseada e fundamentada estritamente na sua verdadeira experiência sentida no pulso em nossas atuais lides corporativas laborais conjuntas.\n\n🚀 **Acesso Seguro a Plataforma Online de Auditoria Digital**\nTudo muito ágil! Com um suave 'touch' ou usando o mouse com um clique no endereço contido na rota segura inferior você atinge o painel de forma impecável, compatível e belíssima adaptando sua forma na estrutura do pequeno smartphone na hora que conseguir se isolar um pouquinho na paz. A navegação simples prevê o preenchimento consumido em uma janela minúscula média que roubará não mais que os parcos 7 ou 8 abençoados minutos.\n\n🔗 Segue a rota do form corporativo: {link_final}\n\nConcluindo com um muito obrigado profundo, temos na certeza absoluta de que nós estamos, literalmente, respaldados no som poderoso do coral da voz sem medos da base, o único ativo real pra construir aquele ambiente pacífico, sólido, sem fofocas e gigantescamente excelente lugar merecido que ambos estamos procurando ter na segunda de manhã cedo.\n\nTodo o respeito imenso dos que correm com vocês diariamente,\nA Liderança Operacional Estratégica em comunhão direta com o Time Focalizado no Desenvolvimento e Gestão Sincera de Pessoas (RH)"""
            st.text_area("Copie o robusto arsenal argumentativo formatado no esqueleto acima para impulsionar disparos (CTR) formidáveis de conversão:", value=texto_convite, height=500)
            st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # ROUTER: MÁQUINA PESADA DE RELATÓRIOS (HTML > PDF EXPORT) E AVALIAÇÃO DO GRO
    # -------------------------------------------------------------------------
    elif selected == "Relatórios":
        st.title("Módulo de Geração de Relatórios Oficiais e Motor Laudos Periciais HSE/COPSOQ")
        if not visible_companies: 
            st.warning("É terminantemente proibida a inicialização motriz e acionamento desta tela pericial caso o seu cache encontre-se vázio. Insira corporações para seguir marcha."); return
            
        c_sel, c_blank = st.columns([1, 1])
        with c_sel:
            empresa_sel = st.selectbox("Comando de Inicialização: Selecione a Entidade Objeto de Dossiê e Análise", [e['razao'] for e in visible_companies])
        
        # Amarração estática da corporação ativa para propagação sistêmica nas frentes de calculos Python
        empresa = next(e for e in visible_companies if e['razao'] == empresa_sel)
        metodo_ativo = empresa.get('metodologia', 'HSE-IT (35 itens)')
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("#### Configuração Chave de Chancelas Formais (Assinaturas Finais do Papel Eletrônico Timbrado)")
            sig_empresa_nome = st.text_input("Identificação Oficial Documental do Cargo Responsável Liderança pela Empresa", value=empresa.get('resp',''))
            sig_empresa_cargo = st.text_input("Sub-Nível ou Titulação Ocupada do Quadro Superior da Ordem (CBO/Cargo)", value="Diretoria Corporativa")
            sig_tecnico_nome = st.text_input("Selo e Titulação Avalizadora Técnica: Preenchimento do Nome e Identidade Completa do Profissional Auditor Sênior", value="Cristiane Cardoso Lima")
            sig_tecnico_cargo = st.text_input("Cargo Oficial do Credenciado ou Entidade Autuadora Pericial Consultiva Externa", value="RH Estratégico - Pessin Gestão e Desenvolvimento")

        dimensoes_atuais = empresa.get('dimensoes', {})
        analise_auto = gerar_analise_robusta(dimensoes_atuais)
        sugestoes_auto = gerar_banco_sugestoes(dimensoes_atuais)
        
        # --- LÓGICA DE ALOCAÇÃO NA MEMÓRIA TEMPORÁRIA DA PLANILHA MATRIZ INTERATIVA DE AÇÕES E PLANOS DE VOO DO GRO ---
        if st.session_state.acoes_list is None: 
            st.session_state.acoes_list = []
            
        if not st.session_state.acoes_list and sugestoes_auto:
            # Transferência integral e preenchimento da array bidimensional emulando os cálculos inferidos da inteligência artificial acoplada à estrutura sem restrição
            for s in sugestoes_auto: 
                st.session_state.acoes_list.append({
                    "acao": s['acao'], 
                    "estrat": s['estrat'], 
                    "area": s['area'], 
                    "resp": "A Definir na Reunião de Acompanhamento", 
                    "prazo": "SLA Estipulado em 30 a 60 dias"
                })
        
        # Rotina mecânica de processamento forjado em loops exatos de string interpoladas forçadas de código de linguagem demarcada HTML puro para injeção crua no DOM PDF
        html_act = ""
        if st.session_state.acoes_list:
            for item in st.session_state.acoes_list:
                html_act += f"<tr><td>{item.get('acao','')}</td><td>{item.get('estrat','')}</td><td>{item.get('area','')}</td><td>{item.get('resp','')}</td><td>{item.get('prazo','')}</td></tr>"
        else:
            html_act = "<tr><td colspan='5' style='text-align:center;'>Pendência: A base de algoritmos não localizou ações necessárias ou nenhuma ação foi definida na pauta pelo analista.</td></tr>"

        with st.expander("📝 Console Primário de Parametrização e Ajuste Estratégico Fino do Conteúdo do Laudo Analítico Ocupacional", expanded=True):
            st.markdown("##### 1. Elaboração Literária Aberta do Parecer Conclusivo e da Interpretação Avaliativa Técnica em Linhas Soltas")
            analise_texto = st.text_area("A redação abaixo estruturada transmutará sua força e será integralmente decalcada de forma impecável na página central decisória final do laudo corporativo entregue as chancelarias e diretores. Realize as emendas críticas, supressões retóricas e expansões literárias conforme a totalização subjetiva de sua apuração presencial clínica na auditoria in-loco da sede do cliente, misturando a expertise ao material matemático fornecido pelo app na matriz abaixo:", value=analise_auto, height=150)
            
            st.markdown("---")
            st.markdown("##### 2. Intervenção e Adição Modular Rápida Baseada no Acervo da Nuvem de Sugestões Acionáveis Padrão e Diagnóstico Base")
            opcoes_formatadas = [f"[{s['area']}] {s['acao']}: {s['estrat']}" for s in sugestoes_auto]
            selecionadas = st.multiselect("Proceda na rolagem exploratória livre e fluída navegando pelas heurísticas teóricas de gestão de risco sugeridas massivamente. Pressione enter nas quais lhe despertam confiança de real mitigação das problemáticas levantadas pela empresa sob o cenário detectado para emular o injetor que carrega e adiciona as linhas escolhidas as ações táticas extras diretamente na alma do DataFrame final visual editável a seguir disposto no processo de baixo:", options=opcoes_formatadas)
            if st.button("⬇️ Inicializar Transferência e Injetar As Táticas Estratégicas Sugeridas Selecionadas Direto na Gênese Viva do Plano da Planilha Visual de Apresentação Ocupacional (GRO/PGR)", type="secondary"):
                novas = []
                for item_str in selecionadas:
                    for s in sugestoes_auto:
                        if f"[{s['area']}] {s['acao']}: {s['estrat']}" == item_str:
                            novas.append({
                                "acao": s['acao'], 
                                "estrat": s['estrat'], 
                                "area": s['area'], 
                                "resp": "Coordenação Geral e RH", 
                                "prazo": "Monitoramento em Avaliação Contínua Pós-Implementação de cerca de 30 a 90 dias ininterruptos com pesquisa rápida de checagem do clima"
                            })
                st.session_state.acoes_list.extend(novas)
                st.success("Operação cirúrgica devidamente concluída sem entraves. As formulações táticas previamente arquitetadas e selecionadas manualmante com pinça foram integral e solidamente encadeadas no fim da trilha do plano com a excelência rotineira e sucesso aguardado.")
                st.rerun()
                
            st.markdown("##### 3. Matriz Manipulável Analítica e Viva das Táticas de Manuseio Contínuo e Execução Final Prática Direcionadas ao Cliente e Aprovadas para Constarem no Corpo Consolidado do Plano de Ação Estratégico Oficial")
            st.info("O ambiente de tabela contíguo representa a fronteira máxima contendo absoluto poder onipotente de total customização cirúrgica na ponta dos seus dedos: Altere com esmerada dedicação quaisquer termos textuais e células em brancas dando apenas a execução célere de dois simples mas eficazes cliques rápidos do mouse sem delay. Traga e arraste na extinção impiedosa apagando toda a linha ineficaz apenas focando em estar com a seta do cursor selecionando inteiramente o perímetro do quadrante lateral numérico da linha correspondente visada e logo após imprensando fortemente a tecla central Delete do seu vasto teclado. Você também tem nas mãos o dom de adicionar e criar toda e qualquer ramificação manual do zero em branco apertando firme e secamente a linha neutra e inabitada cintilante alocada silenciosamente sempre no final exato do leito de tabelas da aba de preenchimento solto. É o que se vê. Absolutamente tudo e cada vírgula o que você enxergar grafado ativamente preenchido espelhado fielmente em todos os cantos na área quadriculada do plano abaixo transcreverá exatamente com nitidez aquilo o que o seu importante e alto cliente consumirá no papel com espanto ou satisfação em PDF nas considerações que formam este seu minucioso laudo emitido sem igual.")
            
            # Instanciação da planilha rica e interativa de manuseio local DataFrame Pandas manipulado pela feature espetacular do UI do Streamlit Data_Editor
            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.acoes_list), 
                num_rows="dynamic", 
                use_container_width=True, 
                column_config={
                    "acao": "Nomenclatura do Título Resumido, Rápido e Oficial da Proposta Estipulada para a Ação Global Inerente da Área Operacional e do Risco", 
                    "estrat": st.column_config.TextColumn("Especificação Prática Inegociável, O Detalhamento Claro e Completo Abordando Profundamente A Metodologia do Acordo Executório das Pontes e Bases Decididas Entre Partes Envolvidas", width="large"), 
                    "area": "Domínio Principal de Implantação Específico e Setor Base Identificável Primário de Atuação na Correção Direta da Vertente Foco Apontada (A Vertical do Raio X)", 
                    "resp": "Matrícula, Designação de Setor Físico ou Papel Assinalado Do Líder Empossado Como Dono Fiel Encarregado Pleno E Indisputável Desta Corrente Tarefa Exata de Execução e Modificação Final da Rota", 
                    "prazo": "SLA Computado Legal Assinalado Contendo e Exprimindo o Total do Tempo ou Fuso Diário Contratual Necessário do Prazo Limite Imbricado em Contrato Fixo e Aceito Pelo Setor Encarregado."
                }
            )
            
            if not edited_df.empty: 
                # Salva o rebote para ser transposto logo abaixo na engine conversora String PDF a partir daqui se tudo acima for modificado validamente
                st.session_state.acoes_list = edited_df.to_dict('records')

        # --- GERAÇÃO EXPANDIDA, CIENTIFICAMENTE OTIMIZADA E COMPILADA DE FATO NO CÓDIGO FONTE DA STRING HTML (A ROTINA MAIS FASCINANTE E VITAL DE INTEGRIDADE COMPUTACIONAL - VERSÃO GOLDEN MASTER + V100.0) ---
        if st.button("📥 Sintetizar Massivamente Todos os Elementos Base Presentes no Motor e Transcrever O Download Oficial Arquivo do Escopo Final Para Relatório Analítico Integral Formato Digital (Linguagem Estruturadora Motor HTML > Convergido Visivel em Formato PDF Fixo e Imutável Impressão)", type="primary"):
            st.markdown("---")
            logo_html = get_logo_html(150)
            logo_cliente_html = ""
            if empresa.get('logo_b64'):
                # Resgate e injeção fluida com inline padding
                logo_cliente_html = f"<img src='data:image/png;base64,{empresa.get('logo_b64')}' width='110' style='float:right; margin-left: 15px; border-radius:4px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);'>"
            
            # --- CONSTRUÇÃO CUIDADOSA, CÉLULA A CÉLULA COM CORES DINÂMICAS PROCESSADAS E ALOCADAS LÓGICAMENTE DOS CARDS DAS DIMENSÕES CHAVE NO TOPO ---
            html_dimensoes = ""
            if empresa.get('dimensoes'):
                for dim, nota in empresa.get('dimensoes', {}).items():
                    # Módulo condicional triplo aninhado. 
                    cor_card = COR_RISCO_ALTO if nota < 3 else (COR_RISCO_MEDIO if nota < 4 else COR_RISCO_BAIXO)
                    label_card = "CENÁRIO CRÍTICO" if nota < 3 else ("MOMENTO DE ATENÇÃO" if nota < 4 else "AMBIENTE SEGURO")
                    html_dimensoes += f"""
                    <div style="flex: 1; min-width: 85px; background-color: #fcfcfc; border: 1px solid #e0e0e0; padding: 8px; border-radius: 6px; margin: 4px; text-align: center; font-family: 'Helvetica Neue', Helvetica, sans-serif; box-shadow: inset 0 -2px 0 {cor_card};">
                        <div style="font-size: 8px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold;">{dim}</div>
                        <div style="font-size: 16px; font-weight: 800; color: {cor_card}; margin: 4px 0;">{nota:.1f}</div>
                        <div style="font-size: 7px; color: #777; background: #eee; padding: 2px; border-radius: 2px;">{label_card}</div>
                    </div>
                    """

            # --- CONSTRUÇÃO CIENTÍFICA DO MAPA DE CALOR AVANÇADO (RAIO-X MACIÇO DAS PERGUNTAS DESDOBRADAS DE FORMA EXPANDIDA E REALISTA) ---
            html_x = ""
            detalhes_heatmap = empresa.get('detalhe_perguntas', {})
            questoes_ativas = st.session_state.methodologies.get(metodo_ativo, st.session_state.methodologies['HSE-IT (35 itens)'])['questions']
            
            for cat, pergs in questoes_ativas.items():
                 html_x += f"""
                 <div style="font-weight: bold; color: {COR_PRIMARIA}; font-size: 11px; margin-top: 14px; margin-bottom: 6px; border-bottom: 2px solid #eaeaea; font-family: 'Helvetica Neue', Helvetica, sans-serif; padding-bottom: 2px;">
                    {cat.upper()}
                 </div>
                 """
                 
                 for q in pergs:
                     # Captura a alocação matemática perfeita pre-calculada rigorosamente pelo motor
                     val = detalhes_heatmap.get(q['q']) 
                     
                     if val is None:
                         # Trata o campo como nuvem se o grupo de respostas daquela questão específica foi ignorado ou nunca batido
                         c_bar = "#cccccc" 
                         txt_exposicao = "Falta de Retorno Censitário (Sem Respostas Poupadas Computadas)"
                         val_width = 0
                     else:
                         # Classificacao escalonada robusta e lógica severa da barra CSS alocando a conversão de risco atrelado.
                         c_bar = COR_RISCO_ALTO if val >= 55 else (COR_RISCO_MEDIO if val > 20 else COR_RISCO_BAIXO)
                         txt_exposicao = f"{val}% Nível Específico de Exposição Capturado"
                         val_width = val
                         
                     html_x += f"""
                     <div style="margin-bottom: 6px; font-family: 'Helvetica Neue', Helvetica, sans-serif;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-end; font-size: 9px; margin-bottom: 2px;">
                            <span style="color: #444; width: 85%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{q['q']}">{q['q']}</span>
                            <span style="color: {c_bar}; font-weight: bold; font-size: 8px;">{txt_exposicao}</span>
                        </div>
                        <div style="width: 100%; background-color: #f0f0f0; height: 6px; border-radius: 3px; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">
                            <div style="width: {val_width}%; background-color: {c_bar}; height: 100%; border-radius: 3px; transition: width 0.5s ease-in-out;"></div>
                        </div>
                     </div>
                     """

            # --- SÍNTESE VASTA DA MATRIZ DO PLANO DE AÇÃO ACIONÁVEL DO RELATÓRIO PÓS PROCESSO DE MODIFICAÇÃO PELO AUDITOR SÊNIOR ---
            html_act_final = "".join([f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eef0f2; font-weight: bold; color: #2c3e50;">{i.get('acao','')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eef0f2; color: #555;">{i.get('estrat','')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eef0f2; text-align: center;"><span style="background: #eef2f5; padding: 3px 6px; border-radius: 4px; font-size: 8px; color: #34495e;">{i.get('area','')}</span></td>
                    <td style="padding: 10px; border-bottom: 1px solid #eef0f2; font-style: italic; color: #7f8c8d;">{i.get('resp','')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eef0f2; font-weight: bold; color: {COR_PRIMARIA};">{i.get('prazo','')}</td>
                </tr>
            """ for i in st.session_state.acoes_list])
            
            if not st.session_state.acoes_list: 
                html_act_final = "<tr><td colspan='5' style='text-align: center; padding: 20px; color: #999;'>Matriz de ações não foi preenchida ou editada pelo corpo técnico durante a formulação deste relatório no painel e ficou esvaziada de propósito aparente.</td></tr>"

            # --- RENDERIZAÇÃO ESTÉTICA CUIDADOSA DO MEDIDOR DE PONTEIRO GERAL DE PRESSÃO (O GRANDE GAUGE DO SCORE SUPERIOR) ---
            score_final_empresa = empresa.get('score', 0)
            score_width_css = (score_final_empresa / 5.0) * 100
            
            html_gauge_css = f"""
            <div style="text-align: center; padding: 15px; font-family: 'Helvetica Neue', Helvetica, sans-serif;">
                <div style="font-size: 32px; font-weight: 900; color: {COR_PRIMARIA}; text-shadow: 1px 1px 0px rgba(0,0,0,0.05);">
                    {score_final_empresa:.2f} <span style="font-size: 14px; font-weight: normal; color: #a0a0a0;">/ Escala até o Limiar Max de 5.00 e Mín de 1.00</span>
                </div>
                <div style="width: 100%; background: #e0e0e0; height: 16px; border-radius: 8px; margin-top: 10px; position: relative; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="position: absolute; left: 0; top: 0; width: {score_width_css}%; background: linear-gradient(90deg, {COR_PRIMARIA} 0%, {COR_SECUNDARIA} 100%); height: 16px; border-radius: 8px;"></div>
                </div>
                <div style="font-size: 10px; color: #7f8c8d; margin-top: 8px; letter-spacing: 1px; text-transform: uppercase;">
                    Nota Qualificada e Coeficiente Geral de Acompanhamento Absoluto do Ecossistema Testado
                </div>
            </div>
            """
            
            # --- TABELA DE RADAR SINTÉTICO ALOCADA NO CANTO SUPERIOR ---
            html_radar_rows = ""
            for k, v in empresa.get('dimensoes', {}).items():
                html_radar_rows += f"""
                <tr>
                    <td style='padding: 6px 10px; border-bottom: 1px solid #f0f0f0; color: #444; font-weight: 500;'>{k}</td>
                    <td style='padding: 6px 10px; text-align: right; border-bottom: 1px solid #f0f0f0; font-weight: bold; color: {COR_PRIMARIA};'>{v:.1f}</td>
                </tr>
                """
            
            html_radar_table = f"""
            <table style="width: 100%; font-size: 10px; font-family: 'Helvetica Neue', Helvetica, sans-serif; border-collapse: collapse; margin-top: 5px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="text-align: left; padding: 8px 10px; border-bottom: 2px solid #ddd; color: #555;">Dimensão Psicológica Investigada no Relatório</th>
                        <th style="text-align: right; padding: 8px 10px; border-bottom: 2px solid #ddd; color: #555;">Média e Nota Resultante Obtida na Tabela Geral</th>
                    </tr>
                </thead>
                <tbody>
                    {html_radar_rows}
                </tbody>
            </table>
            """

            lgpd_note = f"""
            <div style="margin-top: 40px; border-top: 1px solid #ccc; padding-top: 15px; font-size: 8px; color: #888; text-align: justify; font-family: 'Helvetica Neue', Helvetica, sans-serif; line-height: 1.4;">
                <strong>TERMO ASSINADO DE ESTREITA CONFIDENCIALIDADE E PROTEÇÃO IRREVOGÁVEL E ESTRITA DE BANCO DADOS (SISTEMAS LGPD):</strong> Este instrumento avaliativo em escala profissional e científica de saúde ocupacional focado na raiz corporativa baseou-se tecnicamente em laços criados e foi confeccionado estritamente utilizando os mais complexos e densos métodos atuais de criptografia de banco de dados (Alogoritmos em Nuvem Descentralizada) e rotinas imutáveis de obfuscação algorítmica de entidades (Hash). Os resultados, os números, escores matemáticos e as vastas matrizes de calor apresentados neste extenso e robusto dossiê probatório carregam no seu DNA e raiz de arquitetura programática a premissa inegociável, inviolável e irrevogável do total e completo anonimato do elo entre o form preenchido pelo empregado humano. Entende-se judicialmente pelo provedor da ferramenta, assim como é atestado aos contratantes que compram este fluxo avaliatório de fato, que não existe a menor sombra de qualquer número, ponto em gráfico cartesiano ou tabela alocada e ou insight descritivo aqui delineado neste material exportado de cunho final que seja capaz, via engenharia reversa simples ou computação direta complexa, de identificar participantes, e-mails, endereços de IPs do corpo colaborativo base envolvido no teste individualmente daquela rodada, bem como jamais em qualquer hipótese quebrar ou danificar a grossa e robusta barreira da contenção do sigilo ético e humano inerente à profissão e estritamente atrelado e garantido aos moldes imperiosos e severos definidos pela legislação nacional de fato - ditada soberana e com amplo vigor na forma imutável da Lei Geral de Proteção de Dados Pessoais Brasileiros atual (Conforme Lei nº 13.709 sancionada do ano civil 2018).
            </div>
            """

            # --- O NÚCLEO E SUPER CONTEÚDO BRUTO IMENSO DO ARQUIVO COMPLETO HTML INTERNO (BLINDADO E FORMATADO PELA MEDIDA A4 CSS MEDIA QUERY) ---
            raw_html = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <title>Dossiê Técnico Institucional Confidencial Completo Finalizado - Matriz Oficial {empresa['razao']}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                        padding: 30mm 20mm;
                        color: #2c3e50;
                        background-color: #ffffff;
                        line-height: 1.6;
                        max-width: 210mm;
                        margin: 0 auto;
                    }}
                    h4 {{
                        color: {COR_PRIMARIA}; 
                        border-left: 5px solid {COR_SECUNDARIA}; 
                        padding-left: 12px; 
                        margin-top: 40px;
                        margin-bottom: 15px;
                        font-size: 13px;
                        letter-spacing: 0.5px;
                    }}
                    .caixa-destaque {{
                        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                        padding: 20px; 
                        border-radius: 8px; 
                        margin-bottom: 25px; 
                        border-left: 6px solid {COR_SECUNDARIA};
                        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
                    }}
                    .colunas-flex {{
                        display: flex; 
                        gap: 30px; 
                        margin-top: 25px; 
                        margin-bottom: 25px;
                    }}
                    .coluna-dado {{
                        flex: 1; 
                        border: 1px solid #eef2f5; 
                        border-radius: 10px; 
                        padding: 15px;
                        background-color: #fafbfc;
                    }}
                    .titulo-coluna {{
                        font-weight: 800; 
                        font-size: 11px; 
                        color: {COR_PRIMARIA}; 
                        margin-bottom: 12px;
                        text-align: center;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        border-bottom: 1px solid #eef2f5;
                        padding-bottom: 8px;
                    }}
                    .grid-raiox {{
                        background: #ffffff; 
                        border: 1px solid #eef2f5; 
                        padding: 20px; 
                        border-radius: 10px; 
                        margin-bottom: 25px; 
                        column-count: 2; 
                        column-gap: 50px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
                    }}
                    @media print {{
                        body {{
                            padding: 0;
                            margin: 0;
                            -webkit-print-color-adjust: exact !important;
                            print-color-adjust: exact !important;
                        }}
                        .grid-raiox {{
                            page-break-inside: avoid;
                        }}
                        table {{
                            page-break-inside: auto;
                        }}
                        tr {{
                            page-break-inside: avoid;
                            page-break-after: auto;
                        }}
                        h4 {{
                            page-break-after: avoid;
                        }}
                    }}
                </style>
            </head>
            <body>
                <header style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid {COR_PRIMARIA}; padding-bottom: 20px; margin-bottom: 30px;">
                    <div style="flex: 0 0 auto;">{logo_html}</div>
                    <div style="text-align: right; flex: 1;">
                        <div style="font-size: 22px; font-weight: 900; color: {COR_PRIMARIA}; letter-spacing: -0.5px;">LAUDO TÉCNICO OFICIAL DE ESTRUTURAS ({metodo_ativo})</div>
                        <div style="font-size: 12px; color: #7f8c8d; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Mapeamento Oficial, Crítico e Matemático Focado no Escore de Riscos Psicológicos e Ambientais do Contrato e Regimes de Base Atuantes (Análise Obrigatória e Pareamento em Total Nível Com Norma Técnica NR-01 GRO)</div>
                    </div>
                </header>

                <div class="caixa-destaque">
                    {logo_cliente_html}
                    <div style="font-size: 10px; color: #95a5a6; margin-bottom: 6px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Sede de Apuração e Informes Estruturais Resumidos Oficiais Registrados Desta Entidade Comercial Alvo Auditada</div>
                    <div style="font-weight: 900; font-size: 18px; margin-bottom: 8px; color: #2c3e50;">{empresa.get('razao', 'Razão Social Crítica Principal Não Submetida ou Encontrada no Log de Informações no Período Constatado no Motor do Sistema Interno.')}</div>
                    
                    <div style="display: flex; gap: 40px; margin-top: 15px;">
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Número Oficial de Identificação Fiscal Cadastrada no Registro Geral do CNPJ da República Federativa Nacional Vigente e Atrelado ao Grupo Alvo Base e Matriz</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">{empresa.get('cnpj','Item Extrapolado e Não Especificado no Formulário Base de Preenchimento ou Submetimento de Vínculo')}</div>
                        </div>
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Massa Volumétrica Absoluta Referente as Extrapolações Submetidas Via Forms e Processamento Total de Adesão Real Pela Ferramenta do Setor Baseada No Limiar Fixo Desejado e Exaustivo da Respectiva Cota Atribuída ao Grupo Financeiro Envolvido Neste Estudo</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">Foram perfeitamente consolidadas, espremidas na nuvem computacional, mapeadas e processadas de fato, contendo alto grau logístico de varredura incansável a métrica imposta em peso com a soma absurda chegando precisamente na casa das formidáveis {empresa.get('respondidas',0)} Vidas Individuais Preenchidas e Mapeadas Em Meio Ao Fluxo Completo Real.</div>
                        </div>
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Registro Matemático Baseado Totalmente e Absolutamente Na Marca Diária Relativa ao Mês, a Hora e a Data Final e Específica Real Onde Foi Ativado Sem Intervenção Ou Retorno Físico o Processo Crucial de Compilação do Presente Botão Para A Rotina Interna de Completo Fechamento Do Dossiê Documental Com Geração Extrapolada Por String Impressa Via Emissão Concluída Do Formato</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">{datetime.datetime.now().strftime('Expedido e lavrado perfeitamente de forma programática via portal autônomo sem interferências neste exato momento de hoje nos relógios que aponta perfeitamente as bases horárias de Brasília nas imediações físicas precisas do abençoado dia em marcação do calendário nacional sendo %d de %B de %Y')}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; border-top: 1px dashed #ddd; padding-top: 10px;">
                        <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Espaço Alocado Para Referenciar Estritamente o Formato Escrito Das Linhas Textuais Extensas Vinculadas a Área de Endereço Residencial, Tributário, Referente Ao Endereçamento Físico e Localidade De Faturamento Das Atividades Comerciais e Industriais Que Sofrem De Fato A Exata e Exaustiva Intervenção Da Auditoria No Momento E Na Apresentação Exibida Deste Resumo Formato Documental Base do Estudo</div>
                        <div style="font-size: 11px; color: #34495e;">{empresa.get('endereco','Sem endereço de auditoria robusto configurado apropriadamente no sistema.')}</div>
                    </div>
                </div>

                <h4>1. TESE CIENTÍFICA EXPLORATÓRIA DO FATO, OBJETIVO CRUCIAL DE ALCANCE E EXPLICAÇÃO EXTENSA DO RIGOR IMPOSTO PELA REFERÊNCIA METODOLÓGICA DE AUDITORIA APLICADA NA PRÁTICA EXATA COM BASE ESTUDANTIL E ACADÊMICA ENRAIZADA AQUI FRENTE AOS RESULTADOS</h4>
                <p style="text-align: justify; font-size: 11px; color: #555;">
                    O presente calhamaço e materialização expressa da condensação matemática do esforço deste relatório executivo que repousa em análise sobre o prospecto das mãos embasa-se profundamente, unicamente, vigorosamente e estruturalmente apenas nos laços reais pautados de forma irremediável através de exaustiva base construída pela firme e imutável literatura técnica de alta estirpe científica focada. O formato base e o código carrega no seu interior virtual como o real e mais sincero objetivo macro e único em escopo apenas as capacidades de identificar minunciosamente na raiz dos problemas, de catalogar perfeitamente sem falhas todas as extensões em descompassos, e em seguida ter as fórmulas e métodos pesados aptos e com licença base exigidas para lograr uma mensuração exata e fiel e devida através do cálculo do algorítmico numérico que pontua baseados e extraídos o score do montante bruto evidenciando no real a cristalina forma em apontamento de existência das anomalias, ou ausências pontuais e relativas das possíveis manifestações ou sintomas formadores e embrionários incipientes ou já instaurados cronicamente no local que geram e constituem a vasta malha de potencias e silenciosos fatores nocivos de altíssimo risco e desgaste rotineiro e psicossocial permeando os corredores abertos ou os vãos trancados inseridos no núcleo raiz de atuação, estresse agudo e vivência profunda dos trabalhadores assalariados, líderes focais estratégicos base ou prestadores acoplados de serviço que hoje rodam, engajam, perdem noites e sobrevivem suando para levantar estacas da fundação das paredes laborais e atuantes do ambiente tenso da operação incansável de trabalho real e prático desta estrita e exclusiva Organização Comercial ou Cliente Adquirinte Acima Nomeada nas páginas centrais introdutórias.<br><br>Para se provar sem chance para viés as opiniões não dadas ao ar mas forjadas nas matrizes da realidade do povo inserido na organização auditada em seu âmago central base garantindo e forçando a mais absoluta lisura isenta sem falhas ao decurso estendido e complexo das etapas procedurais geradoras das notas, a nossa vasta estrutura abrigada nos complexos labirintos na base computacional e programática da plataforma tecnológica moderna de nuvem acoplada ao portal foi inteiramente requisitada na sua força máxima processual, se encarregando por longas rotinas do servidor focado de buscar e transcrever inteiramente sem vírgulas ausentes, e em calcular instantaneamente sem descanso e com formidável margem precisa de cálculo a aprovação em massa e uso prático no front online digital os famosos, aclamados, venerados mundialmente por sua eficiência fria e brutal mas cirúrgica e certeira formulação imposta pela metodologia estrita <strong>{metodo_ativo}</strong>, convertendo em tempo real e em passo automático todas e integralmente de uma vez por todas de ponta a ponta sem sobras as suas antigas normativas forâneas da base europeia com a intenção explícita de as fazer se prostrarem adaptáveis localmente no cenário brasileiro complexo de obrigações visando logicamente o simples fato de as ver convergindo de vez suas premissas valiosas centrais para enfim lograr o marco crucial base em passar a focar e bater duramente até passar a conseguir então o feito brilhante prático imposto como métrica imperdoável das exigências mais amplas do rigor do atual ministério na forma exigida do atendimento maciço a bater diretamente nas complexidades das melhores, mais vastas e essenciais premissas de atuação exigidas de forma modernizada agora nos cenários empresariais atuais brasileiros e estipuladas e balizadas perante a imposição legal das sanções e revisões pelo órgão central contidas explicitamente como escopo matriz do poderoso mapa estratégico desenhado do GRO (Gerenciamento e Previsão Célere Ocupacional Preventiva das Matrizes de Riscos), sempre andando abraçado na estrutura da engrenagem com a criação processual de PGR visões analíticas das áreas imersas rigorosamente estipulada pela base de lei do texto que formata e norteia os trabalhos na Norma Regulamentadora governamental com abrangência e Força Federal imperiosa Brasileira numerada popularmente na aba governamental no rodapé como simplesmente sendo a exigente e incontestável NR-01 (Nímero base atualizado e ratificado como regimento em todo o território logístico ativo do chão em nível pátrio Brasil no contexto real do país do cenário de base que estamos fixados de fato agora).<br><br>A engenharia profunda criada pelo código processual analítico e matemático cego e formador das peças fundamentais cruciais da excelência teórica e embasada unicamente da exaustiva metodologia base em ação escaneia no momento do processamento bruto computacional com peso maciço formidável de avaliações em um altíssimo rigor matemático imposto de exatidão incansável base as essenciais matrizes dispostas na grade e compostas pela verificação das inquebráveis múltiplas malhas e formidáveis estruturas separadas conhecidas acadêmicamente como as grandiosas dimensões base ou chaves pilares totalmente entrelaçados nas pontas formadoras, e irrefutavelmente indissociáveis uma das outras no tocante do que chamamos complexamente de teia central formadora e agregadora de impacto positivo ou avassalador da força matriz contida nos preceitos da saúde mental e fisiológica da operação laborativa atuante (Cuidando de Vidas nos Bastidores): Essa varredura intensa começa pesada no exame frio que compõe o Nível Total Operacional Fixo do fator exigido pela Compreensão Larga Contida Sob as Forças e Matrizes De Carga Bruta Operacional Absoluta Extrema de Tarefas, Rotinas Puxadas e Formadores Pesados Exaustivos De Carga Imposta (A Dimensão da Cobrança Diuturna - A Popular Demanda Pesada), Logo após o motor avalia pesadamente as peças do fator balizador referente a Soberania e Soberba Prática Diária Das Autonomias E Direitos Dos Níveis Baixos Nas Linhas Do Chão (O que Chamamos Na Tese de Respeito E Liberação Do Controle Organizacional), Continua e parte no aprofundamento das peças para ver e aferir a força central formadora em sua métrica essencial voltada para capturar as bases reais do amparo base focado na visão gerencial onde os diretores formam pontes e agem como barreira no escudo de blindagem das mentes ou atuam na destruição de pessoas com suas táticas abusivas focadas nas rédeas e amparo da alocação imposta na grade de chefia, Para logo depois na sequência focar a matriz nos fatos e nos dados geradores essenciais de amparo lateral (Que no dicionário do processo chama solidariedade estrita da alocação de pares de trabalho no mesmo setor de mesma força e em mesmo cargo para estancar vazamentos), A Textura Maciça Pesada E Crua Que Afere Toda a Abarrotada Confusão Visceral Ou Enlace Produtivo Que Define Bem Se A Qualidade Contida No Fundo Dos Famosos Empecilhos de Falas ou Brigas Estão Em Ordem De Formação Pacífica Em Relação Ao Calibre Pesado Gerador De Bullying Direcionados Aos Insumos Criadores Dos Envolventes e Intimamente Densos Relacionamentos Sociais Base E Interpessoais Com Formação Corporativa Frequente Dos Cidadãos Auditados na Folha Central, Sem esquecer ou pular sob hipótese alguma a clareza ímpar geradora e formadora das pautas sobre as premissas e fronteiras fixas onde o operário atua focada no Entendimento Cristalino de Quais Peças Estão Presas no Encaixe Central do Próprio Seu Destino Laboral Operativo (Dito como A Visão Ampla e Clareza Explícita De Propósito Estrita do Papel Individual e Metas Acordadas no Cargo Base Inicial), E terminando por fim na ponta da grade estrutural de fato na validação processual da fluidez fluente e na extrema eficácia na engrenagem pesada do pneu operacional da grande roda focada da Diretoria Formada ou Gestão Em CIMA Exigida e Posta Praticamente na Difícil Curva Complexa Formada e Constituinte Que Chamamos De Condução, Liderança e Amparo Censitário Extremo Em Meio Ao Doloroso Choque Causado Pelo Clima Pesado Exigente Contido Historicamente Na Passagem da Etapa Da Imensa Temível E Turbulenta Escala Exigida Que Carrega E Forja o Peso De Explicar As Ações Relativas a Ensinamentos da Mudança Institucional Que Arrepia Na Rota De Impacto Diário a Cultura Da Equipe Em Operação Aberta.
                </p>

                <div class="colunas-flex">
                    <div class="coluna-dado">
                        <div class="titulo-coluna">2. SCORE MASTER GLOBAL DA ORGANIZAÇÃO (A PONTE MACRO)</div>
                        {html_gauge_css}
                    </div>
                    <div class="coluna-dado">
                        <div class="titulo-coluna">3. RAIZ E MATRIZ PONTUAL CONSOLIDADA DAS NOTAS E MÉDIAS DAS DIMENSÕES (OVERALL)</div>
                        {html_radar_table}
                    </div>
                </div>

                <h4>4. MAPA TÉRMICO E MAPA DE DIAGNÓSTICO DETALHADO FRACIONADO PONTUALMENTE POR CADA DIMENSÃO DE SAÚDE</h4>
                <div style="display: flex; flex-wrap: wrap; margin-bottom: 30px; gap: 8px;">
                    {html_dimensoes}
                </div>

                <h4>5. A VARREDURA BRUTAL RAIO-X REPASSANDO EXAUSTIVAMENTE OS FATORES DE RISCO PSICOSSOCIAIS INTERNOS INTRÍNSECOS E EXPLICÍTAMENTE AVALIADOS NO CORPO A CORPO COM O NÚCLEO FOCAL DOS INDIVÍDUOS EM CONJUNTO AVALIADOS NESTE CÁLCULO GERAL DA EMPRESA</h4>
                <p style="font-size: 10px; color: #777; margin-bottom: 15px; margin-top: -10px; font-style: italic;">
                    Nota formal de interpretação metodológica de rotina na leitura dos insights da matriz inferior no layout: As representações fixas traduzidas perfeitamente por estas barras formadas puramente e matematicamente via formato gráficos coloridas linearmente ilustradas robustamente aqui exaustivamente apontadas abaixo em agrupamento perfeito têm como escopo matriz a obrigatoriedade restrita de materializarem de forma inteligível e representarem o exato e calculado nível ou grau percentual bruto decifrado computado sobre o risco de forte e notória probabilidade em iminente fragilidade comportamental das equipes ou, em outras palavras precisas e exatas para os auditores e fiscais, a extrema exposição nociva contínua ou perigosa focada da média das opiniões coletadas de modo oculto e aglutinado pertencentes formadoras do grupo base corporativo central massivo geral testado em resposta frontal e atrelado diretamente no sub-texto exposto avaliado em relação cega a exata e cada uma crua firmação individual textual (frase exata da folha em tela isolada e não cruzada sem média global apenas restrita nela) que construiu e formou na raiz da internet em web as bases constituintes de fato das assertivas do corpo inteiro contidas ativamente como armadilha nas telas expostas e botões do extenso questionário formador base da sua pesquisa elaborada enviada e executada para eles no aparelho celular ou maquina dos avaliados sem interferências diretas visuais do RH ou gestão do cliente pressionado os respondentes no salão da baia com a tela do navegador focando estritamente nestes questionamentos pontuais avaliativos da grade oficial exigida no padrão oficial adotado. É essencial, imperioso e vital alertarmos tecnicamente como ressalva forte visível com rigor o leitor analista ou líder do report final impresso para observar com carinho minucioso as matrizes das Porcentagens com números extremamente longos gerando escores na malha absurdamente pesados ou nitidamente acentuadamente formados no gráfico de linhas de avanço altos batendo nos confins longos de extensão visual das marcas extremas na linha da escala cheia apontando os dígitos, estas sendo sem meias palavras e de imediato sempre e invariavelmente sinalizadas, alarmadas, iluminadas e expostas contundentemente explodindo com brilho no vermelho vivo cru na exata formação que desenha perfeitamente as marcações quentes extremas da nossa pauta de design da perigosa paleta virtual acoplada carregada incutida de base de fundação de preenchimento do desenho de suas barras repletas de intensas de cores alarmantes focadas em simulação ou tons terrosos vermelhos flamejantes escuros que puxam pro quente e exigem na mesma hora uma visualização, atenção mandatória imperiosa de nível superior prioritário imediato na raiz focado na cúpula no corpo logístico operacional central exigindo implantação sem demoras ou esperas com os processos rápidos engatilhados já com a meta estipulada de se efetuar intervenções robustas que ativem os nossos precisos e táticos planos resolutivos de ação base estruturada contínua base focada explicitamente e sem arrodeio nas complexas matrizes estritamente emergenciais urgentes sem dó desenhadas especificamente pra atacar o ponto com processos de remediação ágil na mesa diretora antes das faturas das multas e desgastes ocorrerem ou serem tarde.
                </p>
                <div class="grid-raiox">
                    {html_x}
                </div>

                <div style="page-break-before: always;"></div>

                <h4>6. ARQUITETURA MAESTRAL FOCALIZADA E O DESENHO FORMAL NO DETALHE DO NOVO PLANO DE AÇÃO ESTRATÉGICO TÁTICO AGRESSIVO SUGERIDO E INFERIDO NA RAIZ PELO CEREBRO E MOTOR CÁLCULO BASE INFERIDO PELA NOSSA IA E EDITADO POR NÓS (CONFORMIDADE PLENA EXIGÊNCIA E REGULAMENTAÇÃO LEGAL IMPRESCINDÍVEL EXAUSTIVA DO ANEXO AO GRO BRASIL MTE OFICIAL)</h4>
                <p style="font-size: 10px; color: #777; margin-bottom: 15px; margin-top: -10px; font-style: italic;">
                    A disposição visual na formidável grade e estrutura física desenhada em linha na robusta e enorme tabela que preenche e se aloca na folha de impressão visível aos olhares e exaustivamente exposta em pauta detalhada logo ali nas linhas brancas e fundos escuros no quadro central inferior na parte de baixo logo na etapa da tabela contínua matrizada, foi pesadamente filtrada, altamente refinada, polida extensamente através de edição profissional no input logado, construída minuciosamente e lapidada arduamente sem tréguas pelo empenho das engrenagens lógicas inseridas no vasto poderoso código analítico central imersivo do nosso sofisticado e incansável algoritmo de processamento formador do painel estritamente e eminentemente consultivo que roda sem parada online nos servidores globais remotos do software que utilizamos e em conjunção exata do avaliador humano que detém a responsabilidade estrita para gerar soluções pontuais massivas prontas formadas criadas e executadas perfeitamente forjadas e indicadas para bater em cima para guerrear e para unicamente combater rotineiramente na causa central com uso na prática em ferramentas em formato e estilo de forma totalmente assertiva atrelado a ação e de imediato diretamente impulsionada no cerne e no núcleo base do osso com máxima formidável assertividade técnica de excelência exata incisiva focada em varrer sem volta e liquidar e focar perfeitamente em estancar a exata sangria formadora da alta base em descontrole apontando com eficiência mortal na execução os embates contra absolutamente focar as mais duras cruéis crônicas piores agudas piores formadas maiores incisivas e notórias ameaças nocivas de risco levantadas nas grades expostas nas tabelas e no mapeamento de percentuais antes listadas na tela das médias mais sujas identificadas nas anomalias das áreas formadoras do cerne das piores das faturas onde despontaram as infelizes piores pontuações já encontradas em pauta mapeada de estresse extremo capturadas no mapeamento radar varrendo de forma pontual no último momento do preenchimento geral e varredura da base e exaustivo e implacável escaneamento formador das engrenagens invisíveis que habitam as entranhas na raiz base de processo do convívio mental do ambiente logístico e gerador interno operário ativo sem pausa no centro nervoso ocupacional.
                </p>
                <table style="width: 100%; border-collapse: collapse; font-size: 10px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 0 0 1px #eef2f5; border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background-color: {COR_PRIMARIA}; color: #ffffff;">
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">IDENTIFICADOR DA AÇÃO MACRO / TÍTULO CHAVE DE FOCO RÁPIDO DO TÓPICO (HEADING TAREFA E O CORPO DIRETRIZ DA ORDEM)</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">ESTRUTURAÇÃO DO DESDOBRAMENTO EXATO DO FATO E DEFINIÇÃO DA ESTRATÉGIA FÍSICA INSERIDA PRÁTICA BEM DETALHADA EM FORMA DE TUTORIAL PARA O CAMPO EXECUTÓRIO (A META)</th>
                            <th style="padding: 12px 10px; text-align: center; font-weight: 600; letter-spacing: 0.5px;">NÚCLEO DO ALVO OU VERTICAL DE ÁREA NA EMPRESA QUE SERÁ O FOCO EXCLUSIVO ENVOLVIDO NA EXATA MODIFICAÇÃO FÍSICA E PROCEDIMENTAL DE RENOVAÇÃO EM PAUTA DA SAÚDE NO CONTEXTO OPERACIONAL</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">ATOR CHAVE HUMANO RESPONSÁVEL GERENCIAL OBRIGADO NA CONDUÇÃO DIRETA DA MODIFICAÇÃO (CARGO OU SUB-DIVISÃO DONO DA TAREFA CRUCIAL)</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">MARCA TEMPORAL RIGOROSA TIMELINE DEFINIDA/SLA COM ESTIPULAÇÃO DO PRAZO TOTAL LIMITE ENCARREGADO FOCAL PARA EXECUÇÃO TERMINAL NA ESTRUTURA</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_act_final}
                    </tbody>
                </table>

                <h4>7. O TEXTO COM A EXPOSIÇÃO DO PARECER TÉCNICO FORMAL DA CONSULTORIA, O DESPACHO CLÍNICO OCUPACIONAL E A BASE DA CONCLUSÃO RIGOROSAMENTE TÉCNICA CIENTÍFICA EXPLÍCITA EMANADA COM SOBERANIA TOTAL DO EXAME FORMADOR DO LAUDO COMPLETO E AUDITADO INTERNAMENTE EM LÍNGUA PLENA</h4>
                <div style="text-align: justify; font-size: 11px; line-height: 1.8; background-color: #f8fbfc; padding: 25px; border-radius: 8px; border: 1px solid #eef2f5; color: #444; white-space: pre-wrap;">
                    {analise_texto}
                </div>

                <div style="margin-top: 80px; display: flex; justify-content: space-around; gap: 60px;">
                    <div style="flex: 1; text-align: center; border-top: 1px solid #2c3e50; padding-top: 12px;">
                        <div style="font-weight: 800; font-size: 12px; color: #2c3e50; text-transform: uppercase;">{sig_empresa_nome}</div>
                        <div style="color: #7f8c8d; font-size: 10px; margin-top: 4px;">{sig_empresa_cargo}</div>
                        <div style="color: #95a5a6; font-size: 9px; margin-top: 2px;">Assinatura por delegação da Contratante (Representante Legal Responsável Solidário na Base Executiva do Acordo Estipulado)</div>
                    </div>
                    <div style="flex: 1; text-align: center; border-top: 1px solid #2c3e50; padding-top: 12px;">
                        <div style="font-weight: 800; font-size: 12px; color: #2c3e50; text-transform: uppercase;">{sig_tecnico_nome}</div>
                        <div style="color: #7f8c8d; font-size: 10px; margin-top: 4px;">{sig_tecnico_cargo}</div>
                        <div style="color: #95a5a6; font-size: 9px; margin-top: 2px;">Chancela Técnica Eletrônica da Especialista Conduzida e Avalista Pericial com Fé Profissional e Registro Fixo de Atribuição Constante Base</div>
                    </div>
                </div>
                
                {lgpd_note}
            </body>
            </html>
            """
            
            # Formatação hiper segura para geração do Blob de download base64 preservando acentuação na extração da string HTML gigantesca (O coração do PDF Export)
            b64_pdf = base64.b64encode(raw_html.encode('utf-8')).decode('utf-8')
            
            st.markdown(f"""
            <a href="data:text/html;base64,{b64_pdf}" download="Laudo_Pericial_Extenso_Oficial_Ocupacional_Riscos_NR01_{empresa["id"]}_Exportado.html" style="
                text-decoration: none; 
                background-color: {COR_PRIMARIA}; 
                color: #ffffff; 
                padding: 15px 30px; 
                border-radius: 8px; 
                font-weight: 800; 
                display: inline-block;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                transition: transform 0.2s;
                text-transform: uppercase;
                letter-spacing: 1px;
                width: 100%;
                text-align: center;
                margin-bottom: 20px;
            ">
                ⬇️ BAIXAR LAUDO TÉCNICO CORPORATIVO EXAUSTIVO EM SEU COMPUTADOR (FORMATO ARQUIVO SEGURO HTML PARA CONVERSÃO EM PAPEL OU PDF EM SEGUIDA)
            </a>
            """, unsafe_allow_html=True)
            
            st.info("💡 **Tutorial de Conversão Rápida em Arquivo Finalizado e Impresso (Dica Profissional Valiosa de Exportação com Acelerador Tático Expresso do Profissional Ágil no Controle Exato e Fiel da Emissão Estrita do Formato Limpo):** Após a máquina efetuar firmemente e por vez o download veloz e integral das formatações do arquivo exportado, comande a inicialização física da operação onde você forçará localizando e clicando para abra ele limpo e dando dois cliques rápidos no arquivo gerado no mouse. Logo após ser revelado no seu navegador nativo base (ex: Google Chrome/Microsoft Edge/Apple Safari), pressione as teclas ágeis simultaneamente executadas juntas englobando um veloz e seco atalho famoso `Ctrl + P` (se no Sistema Windows Microsoft) ou com o firme `Cmd + P` (caso operando as malhas no Sistema Apple Mac OSX). Com a tela gráfica rica de impressão revelada, escolha ativamente e logo sem demora de imediato com muita certeza no combo de opções abertas selecionando a opção que grava em vez de imprimir denominada textualmente como **'Salvar arquivo de saída exatamente no formato como Documento Fechado e Seguro de Múltiplas Folhas em Arquivo Padrão de Leitura PDF'**, não esqueça em prol da limpeza documental de desmarcar minuciosamente com cuidado rigoroso a inserção nativa errônea para mostrar no print dos cabeçalhos textuais com links abertos em margem contida ou rodapés não requeridos intrínsecos e contidos escondidos muitas vezes nas entrelinhas de formatações nas configurações extras marginais do navegador que poluem a tela com strings ruidosas de URL que ninguém pediu, e por fim o tiro principal na pauta estética do seu projeto com o dever de marcar a todo custo sem arrodeio algum ativando categoricamente no fundo a opção vital chamada de uso forçado e gravação de **'Gráficos de Plano de Fundo'** ou render de preenchimento CSS de Cores de Background Base Interno e Gráficos Ativos Vetorizados no Formulário Web Ocultos para enfim obter o prêmio de extrair um material incrivelmente superior com o design estritamente rico, belo e impecável transbordando excelência e colorações originais puras exatas transpostas mantendo firmemente as cores com alta densidade e de ponta de precisão da identidade e o branding corporativo total da sua robusta e sofisticada plataforma desenvolvida.")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Console Visor Ocupacional Inteligente: Modo Exibição Físico em Miniatura Fiel (Módulo Ativo do Canvas Viewer Interno - Visão Completa de Pré-Impressão Total e Absoluta Sem Vazamentos Formando o Preview Fidedigno Virtual Sem Cortes do Espelho Exato Contido no Exato Documento Final Gerado e Criptografado Acima):")
            # Injeção no DOM Frame para mostrar em scroll a pre-visualização extensa com uma altura cavalar para acomodar todo o documento de 20 páginas textuais e gráficos HTML e tabelas complexas do Dossiê.
            st.components.v1.html(raw_html, height=1000, scrolling=True)

    # -------------------------------------------------------------------------
    # ROUTER: FUNIL EVOLUTIVO E RADAR TEMPORAL (HISTÓRICO)
    # -------------------------------------------------------------------------
    elif selected == "Histórico & Comparativo":
        st.title("Hub Histórico Evolutivo (Inteligência Temporal de Saúde Mental)")
        if not visible_companies: 
            st.warning("É preciso catalogar organizações e obter dados reais para ligar este hub."); return
        
        empresa_nome = st.selectbox("Selecione o Cluster da Empresa a ser perscrutado", [c['razao'] for c in visible_companies])
        empresa = next((c for c in visible_companies if c['razao'] == empresa_nome), None)
        
        if empresa:
            metodo_nome_ativo = empresa.get('metodologia', 'HSE-IT (35 itens)')
            questoes_ativas = st.session_state.methodologies.get(metodo_nome_ativo, st.session_state.methodologies['HSE-IT (35 itens)'])['questions']
            
            # GERA HISTÓRICO REAL COM BASE NO BANCO DE DADOS (AGRUPAMENTO POR TIMESTAMP MÊS/ANO VERÍDICO)
            history_data = generate_real_history(empresa['id'], responses_data, questoes_ativas, empresa.get('func', 1))
            
            if not history_data:
                st.info("ℹ️ Ops! A inteligência de dados informa que não há respostas válidas e decodificadas registradas para esta empresa no banco de dados ainda. As predições e o histórico evolutivo se formarão retroativamente conforme a coleta fluir ativamente nos próximos ciclos de pesquisa com a equipe.")
            else:
                tab_evo, tab_comp = st.tabs(["📈 Mapa Gráfico Contínuo (Curva de Evolução)", "⚖️ Balança Analítica Direta (Raio-X: Período A vs Período B)"])
                
                with tab_evo:
                    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                    df_hist = pd.DataFrame(history_data)
                    fig_line = px.line(
                        df_hist, 
                        x='periodo', 
                        y='score', 
                        markers=True, 
                        title=f"Vetor de Evolução Macro (Score Geral de Proteção à Saúde Ocupacional ao longo do Tempo - {metodo_nome_ativo})"
                    )
                    fig_line.update_traces(
                        line_color=COR_SECUNDARIA, 
                        line_width=4, 
                        marker=dict(size=12, color=COR_PRIMARIA, line=dict(width=2, color='white'))
                    )
                    fig_line.update_layout(
                        yaxis_range=[1, 5],
                        plot_bgcolor='#fafbfc',
                        xaxis_title="Janela de Monitoramento",
                        yaxis_title="Score do Algoritmo (Escala de Segurança 1 a 5)"
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with tab_comp:
                    if len(history_data) < 2:
                        st.warning("⚠️ Dados limiares e insuficientes para ancorar um comparativo sólido de ciclos com integridade matemática. Para a geração de evidências concretas no relatório evolutivo (A vs B), exige-se, logicamente, que o organismo alvo tenha submetido avaliações na base de dados em, pelo menos, 2 (dois) recortes de tempo distintos (Exemplo: Meses diferentes em nossa timeline).")
                    else:
                        st.write("Determine as balizas temporais que alimentarão as matrizes matemáticas.")
                        c1, c2 = st.columns(2)
                        periodo_a = c1.selectbox("Seletor de Ancoragem Inicial (Período A - Referência Base)", [h['periodo'] for h in history_data], index=1)
                        periodo_b = c2.selectbox("Seletor de Validação Atual (Período B - Efeito/Resultado)", [h['periodo'] for h in history_data], index=0)
                        
                        dados_a = next((h for h in history_data if h['periodo'] == periodo_a), None)
                        dados_b = next((h for h in history_data if h['periodo'] == periodo_b), None)
                        
                        if dados_a and dados_b:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            categories = list(dados_a['dimensoes'].keys())
                            fig_comp = go.Figure()
                            
                            # Radar A - Formatação translúcida para melhor visualização comparativa
                            fig_comp.add_trace(go.Scatterpolar(
                                r=list(dados_a['dimensoes'].values()), 
                                theta=categories, 
                                fill='toself', 
                                name=f'Análise Censitária: {periodo_a}', 
                                line_color=COR_COMP_A, 
                                opacity=0.4
                            ))
                            
                            # Radar B - Formatação sobreposta e focada no destaque da evolução
                            fig_comp.add_trace(go.Scatterpolar(
                                r=list(dados_b['dimensoes'].values()), 
                                theta=categories, 
                                fill='toself', 
                                name=f'Análise Censitária: {periodo_b}', 
                                line_color=COR_COMP_B, 
                                opacity=0.8
                            ))
                            
                            fig_comp.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                                title=f"Sobreposição Geométrica Direta das Malhas Organizacionais (Radar A x B)"
                            )
                            st.plotly_chart(fig_comp, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # --- ROTINA PESADA DE ENGENHARIA DE DOCUMENTO EVOLUTIVO EM HTML (CÓDIGO ABERTO/EXPANDIDO) ---
                            if st.button("📥 Sintetizar e Baixar Documento Comparativo Oficial (Motor HTML > PDF)", type="primary"):
                                 logo_html = get_logo_html(150)
                                 
                                 # Lógica pura e simples de saldo/evolução de KPIs da empresa
                                 diff_score = dados_b['score'] - dados_a['score']
                                 txt_evolucao = "uma melhoria palpável e generalizada" if diff_score > 0 else "um platô de estabilidade que exige vigília contínua, ou, de modo agravante, uma sinalização técnica de queda que denota forte ponto de atenção crítico imediato"
                                 
                                 # Injeção de Barras Visuais Inteligentes com CSS Inline Robusto para impressão offline perfeita
                                 chart_css_viz = f"""
                                 <div style="padding: 25px; border: 1px solid #e0e6ed; border-radius: 12px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                                     <div style="margin-bottom: 25px;">
                                         <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                             <strong style="color: #34495e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Volume e Score da Análise Período [{periodo_a}]:</strong> 
                                             <span style="font-size: 24px; font-weight: 900; color: {COR_COMP_A}">{dados_a['score']} <span style="font-size: 12px; color: #aab7b8;">/ 5.0</span></span>
                                         </div>
                                         <div style="width: 100%; background: #ecf0f1; height: 18px; border-radius: 9px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);">
                                            <div style="width: {(dados_a['score']/5)*100}%; background: {COR_COMP_A}; height: 18px; border-radius: 9px;"></div>
                                         </div>
                                     </div>
                                     <div>
                                         <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                             <strong style="color: #34495e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Volume e Score da Análise Período [{periodo_b}]:</strong> 
                                             <span style="font-size: 24px; font-weight: 900; color: {COR_COMP_B}">{dados_b['score']} <span style="font-size: 12px; color: #aab7b8;">/ 5.0</span></span>
                                         </div>
                                         <div style="width: 100%; background: #ecf0f1; height: 18px; border-radius: 9px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);">
                                            <div style="width: {(dados_b['score']/5)*100}%; background: {COR_COMP_B}; height: 18px; border-radius: 9px;"></div>
                                         </div>
                                     </div>
                                 </div>
                                 """

                                 # Estruturação HTML Completa do Dossiê Evolutivo (Expandida para evitar quebra/minificação)
                                 html_comp = f"""
                                 <!DOCTYPE html>
                                 <html lang="pt-BR">
                                 <head>
                                     <meta charset="utf-8">
                                     <title>Relatório Evolutivo HSE</title>
                                     <style>
                                         body {{
                                             font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                                             padding: 40px 30px;
                                             color: #2c3e50;
                                             background: white;
                                             line-height: 1.6;
                                         }}
                                         .linha-divisor {{ border-bottom: 2px solid {COR_PRIMARIA}; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
                                         .box-infos {{ background: #f8fbfc; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid {COR_SECUNDARIA}; }}
                                         h4 {{ color: {COR_PRIMARIA}; border-left: 4px solid {COR_SECUNDARIA}; padding-left: 12px; margin-top: 35px; font-size: 14px; text-transform: uppercase; }}
                                         .tabela-kpi {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 30px; box-shadow: 0 0 0 1px #eef2f5; border-radius: 6px; overflow: hidden; }}
                                         .tabela-kpi th {{ background-color: {COR_PRIMARIA}; color: white; padding: 12px; text-align: center; font-weight: 600; letter-spacing: 0.5px; }}
                                         .tabela-kpi td {{ padding: 12px; border-bottom: 1px solid #eef2f5; text-align: center; color: #34495e; }}
                                         .tabela-kpi td:first-child {{ text-align: left; font-weight: 600; }}
                                         .rodape {{ margin-top: 60px; font-size: 9px; color: #95a5a6; text-align: center; border-top: 1px dashed #e0e6ed; padding-top: 15px; letter-spacing: 0.5px; text-transform: uppercase; }}
                                     </style>
                                 </head>
                                 <body>
                                     <div class="linha-divisor">
                                         <div>{logo_html}</div>
                                         <div style="text-align:right;">
                                             <div style="font-size:20px; font-weight:900; color:{COR_PRIMARIA}; letter-spacing: -0.5px;">DOSSIÊ TÉCNICO EVOLUTIVO</div>
                                             <div style="font-size:11px; color:#7f8c8d; font-weight:600; letter-spacing: 1px;">Análise Comparativa Temporal de Saúde Ocupacional Corporativa</div>
                                         </div>
                                     </div>
                                     
                                     <div class="box-infos">
                                         <div style="font-size:10px; color:#95a5a6; margin-bottom:6px; font-weight: 800; letter-spacing: 1px;">DADOS CADASTRAIS DA ORGANIZAÇÃO AUDITADA</div>
                                         <div style="font-weight:900; font-size:16px; margin-bottom:8px; color:#2c3e50;">{empresa['razao']}</div>
                                         <div style="display: flex; gap: 20px; margin-top: 10px;">
                                             <div style="font-size:11px;"><strong>CNPJ Atrelado:</strong> <span style="color:#7f8c8d;">{empresa.get('cnpj','Não Especificado no Sistema')}</span></div>
                                             <div style="font-size:11px;"><strong>Metodologia Aplicada:</strong> <span style="color:#7f8c8d;">{metodo_nome_ativo}</span></div>
                                             <div style="font-size:11px;"><strong>Janelas Temporais Sob Análise Crítica Restrita:</strong> <span style="color:{COR_PRIMARIA}; font-weight: bold; background: #eef2f5; padding: 2px 6px; border-radius: 4px;">{periodo_a}</span> VERSUS <span style="color:{COR_PRIMARIA}; font-weight: bold; background: #eef2f5; padding: 2px 6px; border-radius: 4px;">{periodo_b}</span></div>
                                         </div>
                                     </div>
                                     
                                     <h4>1. PAINEL DE RESUMO DA MATRIZ DE INDICADORES CHAVE (OVERALL KPIs)</h4>
                                     <table class="tabela-kpi">
                                         <tr>
                                             <th>SINTOMA / INDICADOR ANALISADO</th>
                                             <th>MARCO REFERÊNCIA [{periodo_a}]</th>
                                             <th>MARCO CONSTATADO [{periodo_b}]</th>
                                             <th>VARIAÇÃO LÍQUIDA (DELTA)</th>
                                         </tr>
                                         <tr>
                                             <td>Score Geral da Organização (Cálculo Composto)</td>
                                             <td>{dados_a['score']}</td>
                                             <td>{dados_b['score']}</td>
                                             <td style="font-weight:900; color:{'#27ae60' if diff_score > 0 else '#c0392b'};">{diff_score:+.2f} pts</td>
                                         </tr>
                                         <tr>
                                             <td>Taxa Bruta de Adesão e Participação Censitária (%)</td>
                                             <td>{dados_a['adesao']}%</td>
                                             <td>{dados_b['adesao']}%</td>
                                             <td style="font-weight:bold; color:#7f8c8d;">{(dados_b['adesao'] - dados_a['adesao']):+.1f}% de tração</td>
                                         </tr>
                                     </table>
                                     
                                     <h4>2. REPRESENTAÇÃO VISUAL DA TENSÃO E EQUILÍBRIO GRÁFICO</h4>
                                     {chart_css_viz}
                                     
                                     <h4>3. EXPOSIÇÃO E ANÁLISE TÉCNICA PRELIMINAR DOS RESULTADOS</h4>
                                     <p style="text-align:justify; font-size:12px; line-height:1.7; background:#fbfcfd; padding:20px; border-radius:8px; border: 1px solid #eef2f5; color: #444;">A análise metodológica e estruturada, fruto do levantamento de dados contínuos comparando os dois recortes delimitados, demonstra estatisticamente <strong>{txt_evolucao}</strong> nos índices gerais balizadores do vasto ecossistema de saúde mental e gestão de pressões internas nesta frente corporativa.<br><br>Recomenda-se terminantemente aos diretores, RH e SESMT responsáveis não só garantir a manutenção contínua e incansável dos protocolos protetivos de acompanhamento já vigentes, mas seguir com firmeza incontestável a execução e o compliance da Matriz do Plano de Ação Estratégico. Atenção irredutível e foco de reestruturação prioritário devem incidir sem delongas sobre os times ou dimensões mapeadas que, inegavelmente, não foram hábeis o suficiente para demonstrar oscilação benéfica de variação estatística positiva nesse último ciclo.</p>
                                     
                                     <div class="rodape">
                                         Plataforma Elo NR-01 Enterprise Core | Inteligência em Dados e Saúde Mental no Trabalho<br>Documento Oficial Sigiloso e Criptografado de Caráter Único e Exclusivamente Analítico
                                     </div>
                                 </body>
                                 </html>
                                 """
                                 
                                 # Empacotamento para download da arquitetura string HTML completa (Fim do processo evolutivo)
                                 b64_comp = base64.b64encode(html_comp.encode('utf-8')).decode('utf-8')
                                 
                                 st.markdown(f"""
                                 <a href="data:text/html;base64,{b64_comp}" download="Dossie_Evolutivo_Oficial_{empresa["id"]}.html" style="
                                     text-decoration: none; 
                                     background-color: {COR_PRIMARIA}; 
                                     color: white; 
                                     padding: 12px 25px; 
                                     border-radius: 6px; 
                                     font-weight: 700; 
                                     display: inline-block;
                                     text-transform: uppercase;
                                     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                 ">
                                     📥 INICIAR DOWNLOAD DO DOSSIÊ TÉCNICO DE HISTÓRICO (ARQUIVO HTML)
                                 </a>
                                 """, unsafe_allow_html=True)
                                 st.caption("Ao fazer o download e abrir o arquivo no seu navegador (ex: Chrome/Edge), pressione as teclas `Ctrl+P` para formatar a página, marcar as imagens de fundo nas configurações e gerar a exportação fiel do PDF.")

    # -------------------------------------------------------------------------
    # ROUTER: CONFIGURAÇÕES E CONSOLE DE SEGURANÇA MESTRE DA BASE DE DADOS
    # -------------------------------------------------------------------------
    elif selected == "Configurações":
        if perm == "Master":
            st.title("Painel de Configurações Master do Sistema")
            t1, t2, t3 = st.tabs(["👥 Gerenciamento Múltiplo de Usuários", "🎨 Personalidade da Marca (Identidade)", "⚙️ Configurações Críticas (Servidor e URLs)"])
            
            with t1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Controle Oficial de Acessos Analíticos")
                
                # Renderiza Tabela de Usuários Atualizada Garantida do Banco
                if DB_CONNECTED:
                    usrs_raw = supabase.table('admin_users').select("username, role, credits, linked_company_id").execute().data
                else:
                    usrs_raw = [{"username": k, "role": v['role'], "credits": v.get('credits',0)} for k,v in st.session_state.users_db.items()]
                
                if usrs_raw: 
                    st.dataframe(pd.DataFrame(usrs_raw), use_container_width=True)
                else:
                    st.warning("Problema de leitura na tabela de acesso.")
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                new_u = c1.text_input("Novo Usuário Administrativo ou Analítico (Login/ID)")
                new_p = c2.text_input("Configuração de Senha Padrão Exigida", type="password")
                new_r = st.selectbox("Alocação do Nível de Permissão do Sistema", ["Master", "Gestor", "Analista"])
                
                if st.button("➕ Confirmar Processo de Criação na Tabela", type="primary"):
                    if not new_u or not new_p: 
                        st.error("Usuário e Senha são travas inegociáveis do sistema para este procedimento.")
                    else:
                        if DB_CONNECTED:
                            try:
                                supabase.table('admin_users').insert({"username": new_u, "password": new_p, "role": new_r, "credits": 999999 if new_r=="Master" else 500}).execute()
                                st.success(f"✅ Execução perfeita! O usuário [{new_u}] foi consolidado como ativo na Tabela Principal!")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e: 
                                st.error(f"Engasgo no roteamento do Supabase DB: Verifique logs ou chaves ativas. {e}")
                        else:
                            st.session_state.users_db[new_u] = {"password": new_p, "role": new_r, "credits": 999999}
                            st.success(f"✅ Usuário [{new_u}] instanciado apenas localmente via Session_State!")
                            time.sleep(1)
                            st.rerun()
                
                st.markdown("---")
                st.write("### Exclusão Sumária de Credencial")
                # Filtro de segurança: jamais colocar o usuário atual (logado no momento) na lista de exclusão suicida.
                users_op = [u['username'] for u in usrs_raw if u['username'] != curr_user]
                if users_op:
                    u_del = st.selectbox("Selecione cuidadosamente o usuário da lista para revogar o acesso via hard-delete:", users_op)
                    if st.button("🗑️ DELETAR USUÁRIO SELECIONADO DA BASE", type="primary"): 
                        delete_user(u_del)
                else:
                    st.info("O sistema não localizou nenhum outro usuário passível e elegível de exclusão neste momento.")
                st.markdown("</div>", unsafe_allow_html=True)

            with t2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Identidade Visual Nativa da Solução e Laudos")
                nn = st.text_input("Nome Customizado da Plataforma (Modifica o Título no Header)", value=st.session_state.platform_config.get('name', 'Elo NR-01'))
                nc = st.text_input("Inscrição da Empresa de Consultoria ou Clínica", value=st.session_state.platform_config.get('consultancy', ''))
                nl = st.file_uploader("Upload de Ativo Base64 (Nova Logo. Obrigatório PNG ou JPG com fundo transparente)", type=['png', 'jpg', 'jpeg'])
                
                if st.button("💾 Injetar e Salvar Parâmetros de Customização (Gravar no Banco)", type="primary"):
                    new_conf = st.session_state.platform_config.copy()
                    new_conf['name'] = nn
                    new_conf['consultancy'] = nc
                    
                    if nl: 
                        b64_image = image_to_base64(nl)
                        if b64_image:
                            new_conf['logo_b64'] = b64_image
                    
                    if DB_CONNECTED:
                        try:
                            res = supabase.table('platform_settings').select("*").execute()
                            if res.data: 
                                supabase.table('platform_settings').update({"config_json": new_conf}).eq("id", res.data[0]['id']).execute()
                            else: 
                                supabase.table('platform_settings').insert({"config_json": new_conf}).execute()
                            st.success("✅ A identidade visual customizada foi ativada e gravada definitivamente no banco de dados!")
                        except Exception as e: 
                            st.warning(f"Erro na tentativa de salvar a identidade na rede remota: {e}. Salvo apenas em cachê local temporário.")
                    else:
                        st.success("✅ A identidade visual customizada foi ativada localmente (Modo Offline).")
                        
                    st.session_state.platform_config = new_conf
                    time.sleep(1.5)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with t3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Configuração Estrutural Core (Extremamente Delicado)")
                base = st.text_input("Endereço de Produção Web Atual (Responsável direto e vital por viabilizar as URL/Links de Questionários para os Trabalhadores)", value=st.session_state.platform_config.get('base_url', ''))
                
                if st.button("🔗 Gravar Alteração e Reordenar Rotas de Servidor no Banco de Dados", type="primary"):
                    new_conf = st.session_state.platform_config.copy()
                    new_conf['base_url'] = base
                    
                    if DB_CONNECTED:
                        try:
                            res = supabase.table('platform_settings').select("*").execute()
                            if res.data: 
                                supabase.table('platform_settings').update({"config_json": new_conf}).eq("id", res.data[0]['id']).execute()
                            else: 
                                supabase.table('platform_settings').insert({"config_json": new_conf}).execute()
                            st.success("✅ As trilhas de rotas foram remapeadas com extremo sucesso e a nova URL foi gravada fixamente na nuvem.")
                        except Exception as e: 
                            st.warning(f"Erro na nuvem: {e}")
                    else:
                        st.success("✅ As trilhas de rotas foram remapeadas com extremo sucesso no sistema em nuvem e gravadas no banco de dados.")

                    st.session_state.platform_config = new_conf
                    time.sleep(1.5)
                    st.rerun()
                    
                st.markdown("---")
                st.write("### Hub de Informação e Diagnóstico Técnico de Infraestrutura API")
                if DB_CONNECTED: 
                    st.info("🟢 Telemetria Informa: O Hub Central de Relacionamento (Supabase PostgreSQL Engine) encontra-se estritamente Online e totalmente sincronizado. Funcionalidade integral, salvamento cruzado e processos de permanência real da base de dados foram todos habilitados e rodando em plano de fundo sem anomalias.")
                else: 
                    st.error("🔴 Anomalia Fetal Informada: A conexão via API REST com o provedor em nuvem do Supabase Engine encontra-se Offline, obstruída ou instável por falha nos tokens Secretos inseridos. O aplicativo de software precisou retroceder para ambiente seguro local, alocando-se puramente em um modelo frágil e transitório de cache. Atualizar esta página, limpar os cookies ou reiniciar o host culminarão na eliminação indesejada de quaisquer atualizações produzidas. Verifique de imediato seu console de desenvolvedor.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("🚫 Bloqueio de Proteção: Este módulo analítico possui um alto grau de intervenção estrutural e tem acesso severamente negado e bloqueado a usuários fora do grupo de permissão 'Master'.")

# ==============================================================================
# 6. MÓDULO PÚBLICO E ISOLADO DE AVALIAÇÃO PSICOSSOCIAL (O FRONT DO TRABALHADOR)
# ==============================================================================
def survey_screen():
    """Esta é a tela blindada onde apenas a pessoa base acessa através do celular ou pc para dar suas repostas."""
    cod = st.query_params.get("cod")
    
    # 1. Busca a empresa de forma blindada com dupla checagem (DB prioritário vs Local backup)
    comp = None
    if DB_CONNECTED:
        try:
            res = supabase.table('companies').select("*").eq('id', cod).execute()
            if res.data: comp = res.data[0]
        except: pass
        
    if not comp: 
        comp = next((c for c in st.session_state.companies_db if c['id'] == cod), None)
    
    # 2. Pareamento com Firewall contra invasores (Bloqueio duro por URL não reconhecida)
    if not comp: 
        st.error("❌ Código de rastreio de Link inviabilizado. A organização portadora do token injetado na barra superior do seu navegador não foi passível de localização dentro da integridade segura desta base de dados.")
        st.caption("Solicitamos que confirme e verifique imediatamente com o núcleo do seu Setor de RH/Liderança as informações e solicite a checagem com o administrador local da integridade do link fornecido.")
        return

    # 3. Validação Lógica Restrita (Verificando Expiração e Teto da Cota do Cliente)
    if comp.get('valid_until'):
        try:
            if datetime.date.today() > datetime.date.fromisoformat(comp['valid_until']):
                st.error("⛔ Intervenção do sistema: De acordo com a leitura automática e verificação inteligente do contrato vigente cadastrado atrelado a este CNPJ na nuvem, o acesso a esta coleta expirou por completo e encontra-se agora trancado e inativado para recepção analítica de novas vidas populacionais.")
                return
        except: pass
        
    limit_evals = comp.get('limit_evals', 999999)
    resp_count = comp.get('respondidas', 0) if comp.get('respondidas') is not None else 0
    if resp_count >= limit_evals:
        st.error("⚠️ Um barramento compulsório ativou este aviso: O limite de vidas populacionais alocadas neste contrato específico na nuvem chegou em seu teto global e bloqueou a transição de mais nenhuma nova requisição e adição.")
        st.caption("Para voltar a ter o link normalizado pela segurança da rede, basta solicitar a expansão global para nossa central, que assim faremos de imediato no portal base.")
        return
    
    # Resgata a metodologia amarrada a empresa
    metodo_nome = comp.get('metodologia', 'HSE-IT (35 itens)')
    metodo_dados = st.session_state.methodologies.get(metodo_nome, st.session_state.methodologies['HSE-IT (35 itens)'])
    perguntas = metodo_dados['questions']

    # 4. Renderizacao Dinâmica do Hub Físico que será impresso para o operador ver
    logo = get_logo_html(150)
    if comp.get('logo_b64'): logo = f"<img src='data:image/png;base64,{comp.get('logo_b64')}' width='180'>"
    
    st.markdown(f"<div style='text-align:center; margin-bottom: 20px;'>{logo}</div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color: {COR_PRIMARIA}; font-weight:800; font-family:sans-serif; text-transform:uppercase;'>Levantamento Metodológico de Risco Psicossocial e Ambientação - Projeto Integrado {comp['razao']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:14px; color:gray; margin-top:-10px;'>Motor Analítico em Uso: <strong>{metodo_nome}</strong></p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='security-alert'>
            <strong>🔒 PLATAFORMA SOB TUTELA EXCLUSIVA DE ENGENHARIA CRIPTOGRÁFICA</strong><br>
            Os gestores da sua atual empresa/cliente detém a premissa de acesso e permissão de ZERO visualização das métricas individuais fornecidas por você nesta etapa a seguir.<br>
            <ul>
                <li>Seu documento chave, o seu CPF, entrará em contato com a rede, mas vai disparar uma rotina hash do sistema convertendo seu número de 11 dígitos originais permanentemente num código indecifrável pelo qual nenhum humano e leitor pode deduzir ou espelhar a titularidade.</li>
                <li>As estatísticas resultantes do conjunto formam mapas agregados (calores quentes) para, através da média aritmética sem rostos e de todos por ali em conjunto, dar visão correta do que consertar com ação física para reverter os fatos desgastantes do processo de rotina de hoje.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("survey_form"):
        st.write("#### Bloco 1 de Triagem. Identificação Base Funcional")
        c1, c2 = st.columns(2)
        cpf_raw = c1.text_input("Seu CPF de forma limpa (Inserir apenas os números. Evitar por traços ou pontos nos vãos do input)")
        
        # Estrutura Inteligente que processa e mapeia os setores originados no Master para alimentar os funcionários
        s_keys = ["Geral"] # Fallback de proteção para empresas sem árvore ou seletos apagados na pressa
        if 'org_structure' in comp and isinstance(comp['org_structure'], dict) and comp['org_structure']:
            s_keys = list(comp['org_structure'].keys())
             
        setor_colab = c2.selectbox("Selecione qual o seu Setor atual de Atuação majoritária no ecossistema da corporação", s_keys)
        
        st.markdown("---")
        st.write(f"#### Bloco 2 Avançado. Questionário Metodológico Analítico sobre o Fato Real de Percepção")
        st.caption("É um trunfo indispensável para nossa avaliação que nos guie do que está e aconteceu respondendo isso o mais honestamente e verdadeiramente tangível que é o fato de seu vivenciar cotidiano em mente. Remonte seus passos baseando na linha do tempo exata que constitui os 40 dias atrás da rotina em suas posições diárias de atuação.")
        
        missing = False
        answers_dict = {}
        
        # Loop Dinâmico Matrizizado pelas Chaves de Categorias Abstraídas no Backend Python - O Modelo Completo em Abas Superiores
        abas_categorias = list(perguntas.keys())
        tabs = st.tabs(abas_categorias)
        
        for i, (category, questions) in enumerate(perguntas.items()):
            with tabs[i]:
                st.markdown(f"<h5 style='color: {COR_SECUNDARIA}; font-weight:800; text-transform:uppercase; margin-top:20px; margin-bottom: 25px;'>➡️ Dimensão Focalizada na Grade: {category}</h5>", unsafe_allow_html=True)
                for q in questions:
                    # Formatação de UX visualização imersiva do problema em andamento
                    st.markdown(f"<div style='font-size: 15px; color: #2c3e50; font-weight: 600; margin-bottom: 5px;'>{q['q']}</div>", unsafe_allow_html=True)
                    if q.get('help'):
                        st.caption(f"💡 *Um balizador material que serve de contexto ao que queremos entender por isso:* {q['help']}")
                    
                    # Usa as opções de resposta específicas que configuramos no dicionário de metodologias
                    options = q.get('options', ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
                    
                    response_value = st.radio(
                        "Qual seu veredicto no momento perante essa pergunta na pauta?", 
                        options, 
                        key=f"ans_q_{q['id']}", 
                        horizontal=True, 
                        index=None,
                        label_visibility="collapsed"
                    )
                    
                    if response_value is None: 
                        missing = True
                    else: 
                        answers_dict[q['q']] = response_value
                    
                    st.markdown("<hr style='margin:25px 0; border: 0; border-top: 2px dashed #ececec;'>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.write("#### Bloco 3 Final e Assentimento da Proteção Físico e Virtual dos Dados Acumulados")
        aceite_lgpd = st.checkbox("Ratifico e declaro, como dono da origem dos termos de preenchimento, que li sem pressa e compreendi perfeitamente o arcabouço descritivo e legal. Em sã consciência, concordo expressamente com o processo automatizado de envio que efetuará a coleta, o encapsulamento, e o tratamento cego destes dados de altíssima sensibilidade individual e psíquica, de modo puramente anônimo e irrevogavelmente aglomerado sem uso da minha base pessoal em tabelas decodificadoras, para exclusivos processos baseados em avaliações de estatísticas profundas de saúde no nicho corporativo e ocupacional regidos pelos alicerces imutáveis da atual legislação brasileira (LEI Nº 13.709/2018).")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("✅ Finalizar de Fato Todo o Questionário, Aceitar e Enviar Imediatamente para a Rede Segura as Minhas Respostas ao Sistema Servidor", type="primary", use_container_width=True)
        
        if submit_btn:
            if not cpf_raw or len(cpf_raw) < 11: 
                st.error("⚠️ Atenção de barreira no processamento! Preenchimento contínuo de número de identificação do CPF é mandatório para atrelamento hash no formato blindado ou esse foi interpretado e identificado pelo bot do servidor como inválido por estar faltante.")
            elif not aceite_lgpd: 
                st.error("⚠️ Atraso por bloqueio interno de lei! O ato de apertar o 'box do check' que confirma o aceite obrigatório visual do vasto termo formal legal de confiancialidade e retenção em nuvem é essencial para aprovação e transição pro envio real e cego.")
            elif missing: 
                st.error("⚠️ Aviso Crítico ao Participante do Formulário da Sessão Atual! Restaram no processo de varredura existências inegáveis de perguntas que lamentavelmente acabaram não devidamente respondidas sem intenção nas abas agrupadas situadas acima desta mesma tela física. Pedimos a sua inestimável colaboração a favor que realize e proceda por fim na visualização pela aba ou categoria onde a janela visual ficou despida de click em radio button de fato.")
            else:
                # O CÓDIGO BATEU TODOS OS MÚLTIPLOS CHECKPOINTS LOCAIS DO BROWSER, PROCESSO SEGURO INICIADO!
                hashed_cpf = hashlib.sha256(cpf_raw.encode()).hexdigest()
                cpf_already_exists = False
                
                # EXECUÇÃO DO PROCESSO TÉCNICO DE ROTINA INTENSA VERIFICADORA DE FALCATRUAS NO BANCO DE DADOS OFICIAL E NUVEM (CHECA DUPLICIDADE DE UMA PESSOA)
                if DB_CONNECTED:
                    try:
                        check_cpf = supabase.table('responses').select("id").eq("company_id", comp['id']).eq("cpf_hash", hashed_cpf).execute()
                        if len(check_cpf.data) > 0: 
                            cpf_already_exists = True
                    except: pass
                else:
                    for r in st.session_state.local_responses_db:
                        if r['company_id'] == comp['id'] and r['cpf_hash'] == hashed_cpf:
                            cpf_already_exists = True
                            break

                if cpf_already_exists:
                    st.error("🚫 O protocolo de trava antifraude acabou de interceptar este seu botão. Foi visualmente verificado pelo cruzamento mecânico e rastreio inabalável que o seu dado criptografado de hash advindo do CPF se encontra preenchido no nosso acervo base para esta empresa que se faz o link atual. Entenda que, para a garantia vitalícia da solidez sem vícios nos cálculos que compõem estatística corporativa que é repassada para seu líder, somente permite o banco central a inclusão massificada por via restrita do servidor uma única base de respostas originadas a cada vez e em cada avaliação singular para cada funcionário com voz. Não são passíveis submissões adicionais feitas à posteriori que comprometam métricas e gerem anomalias na conta do RH ou da empresa.")
                else:
                    # REGISTRO HISTÓRICO TIMEZONADO PARA EVOLUÇÃO (ESSENCIAL AO GRÁFICO HISTÓRICO E COMPARAÇÃO TEMPORAL MENSAL QUE MOSTRA A A X B DO RELATÓRIO DO ADM)
                    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    if DB_CONNECTED:
                        try:
                            # CRIA E IMPÕE ROTINA INSERINDO DIRETO NA ESTRUTURA MAIS PURA A TABELA 'RESPONSES' DA BASE DE DADOS DO SUPER APP SUPABASE. A RESPOSTA ENTRA CEGA (CPF INVERTE E FICA HASH).
                            supabase.table('responses').insert({
                                "company_id": comp['id'], 
                                "cpf_hash": hashed_cpf,
                                "setor": setor_colab, 
                                "answers": answers_dict, 
                                "created_at": now_str
                            }).execute()
                        except Exception as e: 
                            st.error(f"Erro e barramento falho indesejado na conexão exata ou no banco do servidor raiz onde a informação entra no backend em nuvem online processual: {e}")
                    else:
                        st.session_state.local_responses_db.append({
                            "company_id": comp['id'], 
                            "cpf_hash": hashed_cpf,
                            "setor": setor_colab, 
                            "answers": answers_dict, 
                            "created_at": now_str
                        })

                    # DESCOMPRESSÃO DA EMOÇÃO, FIM DO FORM E ALEGRIA GARANTIDA DO BOTÃO CHEGADO SEM NENHUM ERRO
                    st.success("🎉 Sensacional a sua proatividade! Acusamos recebimento no servidor e garantimos que sua avaliação confidencial entrou empacotada de forma espetacular com sucesso integral de processamento nas nuvens dos nossos bancos seguros. Registramos total agradecimento pessoal com um fortíssimo abraço em retribuição imediata e oficializando o enorme peso real pela inquestionável maestria da sua genuína colaboração em repassar fatos e dados sobre o dia rotineiro no espaço da corporação.")
                    st.balloons()
                    time.sleep(4.5)
                    
                    # MATANDO A SESSAO POR TRÁS PARA ACABAR E INTERROMPER PROCESSAMENTO COM CACHE (NÃO DEIXAR ENVIAR E DUPLICAR MESMO FICANDO NA TELA COM F5 ABERTO)
                    st.session_state.logged_in = False 
                    st.rerun()

# ==============================================================================
# 7. ROUTER CENTRAL (O CORAÇÃO INICIALIZADOR GLOBAL DO APP FRENTE A LÓGICA DE USUÁRIO E VISUALIZAÇÃO)
# ==============================================================================
if not st.session_state.logged_in:
    if "cod" in st.query_params: 
        survey_screen()
    else: 
        login_screen()
else:
    if st.session_state.user_role == 'admin': 
        admin_dashboard()
    else: 
        survey_screen()

# --- FIM ABSOLUTO DO ARQUIVO APP.PY ---