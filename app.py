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
    page_title="Elo NR-01 | Gestão de Saúde Mental",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Conexão com o Supabase
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False

# ------------------------------------------------------------------------------
# 1.1. CONFIGURAÇÕES GERAIS E IDENTIDADE VISUAL
# ------------------------------------------------------------------------------
def get_saved_settings():
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

COR_PRIMARIA = "#003B49"    
COR_SECUNDARIA = "#40E0D0"  
COR_FUNDO = "#f4f6f9"
COR_RISCO_ALTO = "#ef5350"      # Vermelho (Atenção)
COR_RISCO_MEDIO = "#ffa726"     # Laranja/Amarelo (Moderado)
COR_RISCO_BAIXO = "#66bb6a"     # Verde (Saudável)
COR_COMP_A = "#3498db"          # Azul
COR_COMP_B = "#9b59b6"          # Roxo

# ==============================================================================
# 2. FOLHA DE ESTILOS EM CASCATA (CSS)
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
    
    /* Espaçamento elegante para os radio buttons nativos do Streamlit sem quebrar os quadrados */
    div[role="radiogroup"] {{ gap: 15px; padding-top: 5px; padding-bottom: 15px; }}

    @media print {{
        [data-testid="stSidebar"], .stButton, header, footer, .no-print {{ display: none !important; }}
        .a4-paper {{ box-shadow: none; margin: 0; padding: 0; width: 100%; max-width: 100%; }}
        .stApp {{ background-color: #ffffff; }}
        .chart-container {{ border: none; box-shadow: none; padding: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. VARIÁVEIS DE SESSÃO
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
# 3.1. BANCO DE METODOLOGIAS (HSE + COPSOQ) - ADAPTADO PARA PT-BR
# ------------------------------------------------------------------------------
if 'methodologies' not in st.session_state:
    # Definição das escalas variadas
    escala_freq = ["Nunca/Quase Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"]
    escala_conc = ["Discordo Totalmente", "Discordo", "Neutro", "Concordo", "Concordo Totalmente"]
    escala_int = ["Nada/Quase Nada", "Um pouco", "Moderadamente", "Muito", "Extremamente"]
    escala_sat = ["Muito Insatisfeito", "Insatisfeito", "Neutro", "Satisfeito", "Muito Satisfeito"]
    escala_sau = ["Deficitária", "Razoável", "Boa", "Muito Boa", "Excelente"]
    
    st.session_state.methodologies = {
        "HSE-IT (35 itens)": {
            "desc": "Focado em 7 dimensões de gestão de estresse (Padrão UK/Brasil).",
            "questions": {
                "Demandas": [
                    {"id": "h1", "q": "Tenho prazos impossíveis de cumprir?", "rev": True, "options": escala_freq, "help": "Exemplo: Ser cobrado rotineiramente por entregas urgentes no final do dia."},
                    {"id": "h2", "q": "Sou pressionado a trabalhar longas horas?", "rev": True, "options": escala_freq, "help": "Exemplo: Sentir que apenas o seu horário normal não é suficiente para a empresa."},
                    {"id": "h3", "q": "Tenho que trabalhar muito intensamente?", "rev": True, "options": escala_freq, "help": "Exemplo: Não ter tempo nem para fazer uma pequena pausa devido ao volume de demandas."},
                    {"id": "h4", "q": "Tenho que negligenciar algumas tarefas?", "rev": True, "options": escala_freq, "help": "Exemplo: Ter que fazer as coisas com menos qualidade para dar tempo de entregar tudo."},
                    {"id": "h5", "q": "Não consigo fazer pausas suficientes?", "rev": True, "options": escala_freq, "help": "Exemplo: Precisar encurtar a hora de almoço frequentemente."},
                    {"id": "h6", "q": "Sou pressionado por diferentes grupos?", "rev": True, "options": escala_freq, "help": "Exemplo: Receber ordens urgentes e contraditórias de pessoas diferentes."},
                    {"id": "h7", "q": "Tenho que trabalhar muito rápido?", "rev": True, "options": escala_freq, "help": "Exemplo: O ritmo exigido é sempre acelerado e desgastante."},
                    {"id": "h8", "q": "Tenho prazos irrealistas?", "rev": True, "options": escala_freq, "help": "Exemplo: Metas que a equipe raramente consegue atingir de forma saudável."}
                ],
                "Controle": [
                    {"id": "h9", "q": "Posso decidir quando fazer uma pausa?", "rev": False, "options": escala_freq, "help": "Exemplo: Ter a liberdade de se levantar ou ir ao banheiro sem pedir autorização."},
                    {"id": "h10", "q": "Tenho liberdade para decidir como faço o meu trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo: Poder escolher o melhor método ou ferramenta para atingir os resultados."},
                    {"id": "h11", "q": "Tenho poder de decisão sobre o meu ritmo?", "rev": False, "options": escala_freq, "help": "Exemplo: Poder gerenciar os seus picos de energia durante o dia."},
                    {"id": "h12", "q": "Eu decido quando vou realizar cada tarefa?", "rev": False, "options": escala_freq, "help": "Exemplo: Ter autonomia para organizar a sua própria agenda diária."},
                    {"id": "h13", "q": "Tenho voz sobre como o meu trabalho é realizado?", "rev": False, "options": escala_freq, "help": "Exemplo: Suas ideias de melhoria são ouvidas e valorizadas pela gestão."},
                    {"id": "h14", "q": "O meu horário de trabalho pode ser flexível?", "rev": False, "options": escala_freq, "help": "Exemplo: Ter acesso a banco de horas ou acordos amigáveis com a liderança."}
                ],
                "Suporte do Gestor": [
                    {"id": "h15", "q": "Recebo feedback sobre o trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo: O seu gestor conversa com você de forma clara e respeitosa sobre o seu desempenho."},
                    {"id": "h16", "q": "Posso contar com o meu superior diante de um problema?", "rev": False, "options": escala_freq, "help": "Exemplo: Saber que o gestor vai ajudar a resolver uma falha, em vez de apenas culpá-lo."},
                    {"id": "h17", "q": "Posso falar com o meu superior sobre algo que me chateou?", "rev": False, "options": escala_freq, "help": "Exemplo: Sentir que existe um espaço seguro para conversas sinceras."},
                    {"id": "h18", "q": "Sinto o apoio do meu gestor(a)?", "rev": False, "options": escala_freq, "help": "Exemplo: Sentir que a sua chefia se importa de forma genuína com o seu bem-estar."},
                    {"id": "h19", "q": "Meu gestor me motiva no trabalho?", "rev": False, "options": escala_freq, "help": "Exemplo: Receber elogios e reconhecimento quando faz um bom trabalho."}
                ],
                "Suporte dos Colegas": [
                    {"id": "h20", "q": "Recebo a ajuda e o apoio que preciso dos meus colegas?", "rev": False, "options": escala_freq, "help": "Exemplo: A equipe é unida e ajuda-se mutuamente nos momentos de maior pressão."},
                    {"id": "h21", "q": "Recebo o respeito que mereço dos meus colegas?", "rev": False, "options": escala_freq, "help": "Exemplo: O tratamento diário é cordial e livre de preconceitos."},
                    {"id": "h22", "q": "Meus colegas estão dispostos a ouvir meus problemas?", "rev": False, "options": escala_freq, "help": "Exemplo: Ter com quem desabafar sobre um dia difícil ou um cliente complicado."},
                    {"id": "h23", "q": "Meus colegas me ajudam em momentos difíceis?", "rev": False, "options": escala_freq, "help": "Exemplo: A equipe divide o esforço quando o volume de trabalho está muito alto."}
                ],
                "Relacionamentos": [
                    {"id": "h24", "q": "Estou sujeito a desrespeito pessoal?", "rev": True, "options": escala_freq, "help": "Exemplo: Ouvir comentários desrespeitosos, constrangedores ou pressões indevidas."},
                    {"id": "h25", "q": "Existem atritos ou conflitos entre colegas?", "rev": True, "options": escala_freq, "help": "Exemplo: O ambiente é marcado por fofocas, divisões ou discussões frequentes."},
                    {"id": "h26", "q": "Sinto-me isolado ou sofro bullying?", "rev": True, "options": escala_freq, "help": "Exemplo: Ser excluído de propósito de conversas de trabalho ou ser alvo de piadas de mau gosto."},
                    {"id": "h27", "q": "Os relacionamentos no trabalho são tensos?", "rev": True, "options": escala_freq, "help": "Exemplo: Sentir que precisa 'pisar em ovos' ao falar com as pessoas por receio de reações exageradas."}
                ],
                "Papel na Empresa": [
                    {"id": "h28", "q": "Sei claramente o que é esperado de mim?", "rev": False, "options": escala_conc, "help": "Exemplo: As suas metas e tarefas diárias estão bem definidas e acordadas."},
                    {"id": "h29", "q": "Sei como fazer para executar o meu trabalho?", "rev": False, "options": escala_conc, "help": "Exemplo: Você recebeu o treinamento e as ferramentas certas para desempenhar bem a sua função."},
                    {"id": "h30", "q": "Sei quais são os objetivos do meu departamento?", "rev": False, "options": escala_conc, "help": "Exemplo: Compreende para onde a sua equipe está caminhando estrategicamente."},
                    {"id": "h31", "q": "Tenho noção clara das minhas responsabilidades?", "rev": False, "options": escala_conc, "help": "Exemplo: Os limites da sua função, até onde pode agir e decidir, estão bem claros."},
                    {"id": "h32", "q": "Entendo a minha importância na empresa?", "rev": False, "options": escala_conc, "help": "Exemplo: Consegue ver como o seu trabalho diário ajuda no sucesso do negócio."}
                ],
                "Gestão de Mudança": [
                    {"id": "h33", "q": "Tenho oportunidade de tirar dúvidas sobre mudanças?", "rev": False, "options": escala_conc, "help": "Exemplo: Haver um espaço seguro para esclarecimentos quando uma nova regra ou sistema é implementado."},
                    {"id": "h34", "q": "Sou consultado(a) sobre mudanças no meu trabalho?", "rev": False, "options": escala_conc, "help": "Exemplo: A liderança pede a opinião de quem realiza a tarefa antes de mudar um processo."},
                    {"id": "h35", "q": "Quando há mudanças, fica claro como vão funcionar?", "rev": False, "options": escala_conc, "help": "Exemplo: A comunicação da empresa é transparente e bem explicada."}
                ]
            }
        },
        "COPSOQ II (Versão Média PT)": {
            "desc": "Versão Média Oficial (76 itens - Adaptação PT-BR). Avalia de forma profunda exigências, saúde e valores no ambiente laboral.",
            "questions": {
                "Exigências Laborais (Quantidade e Ritmo)": [
                    {"id": "c1", "q": "Sua carga de trabalho se acumula por ser mal distribuída?", "rev": True, "options": escala_freq},
                    {"id": "c2", "q": "Com que frequência você não tem tempo para completar todas as tarefas do seu trabalho?", "rev": True, "options": escala_freq},
                    {"id": "c3", "q": "Precisa fazer horas extras?", "rev": True, "options": escala_freq},
                    {"id": "c4", "q": "Precisa trabalhar muito rapidamente?", "rev": True, "options": escala_freq},
                    {"id": "c5", "q": "O seu trabalho exige a sua atenção constante?", "rev": True, "options": escala_freq},
                    {"id": "c6", "q": "Seu trabalho exige que você seja bom em propor novas ideias?", "rev": False, "options": escala_freq},
                    {"id": "c7", "q": "O seu trabalho exige que tome decisões difíceis?", "rev": True, "options": escala_freq},
                    {"id": "c8", "q": "Seu trabalho exige muito de você emocionalmente?", "rev": True, "options": escala_freq}
                ],
                "Organização e Influência": [
                    {"id": "c9", "q": "Você tem um alto grau de influência no seu trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c10", "q": "Participa na escolha das pessoas com quem trabalha?", "rev": False, "options": escala_freq},
                    {"id": "c11", "q": "Pode influenciar a quantidade de trabalho que compete a você?", "rev": False, "options": escala_freq},
                    {"id": "c12", "q": "Tem alguma influência sobre o tipo de tarefas que faz?", "rev": False, "options": escala_freq},
                    {"id": "c13", "q": "O seu trabalho exige que tenha iniciativa?", "rev": False, "options": escala_freq},
                    {"id": "c14", "q": "O seu trabalho permite que você aprenda coisas novas?", "rev": False, "options": escala_freq},
                    {"id": "c15", "q": "O seu trabalho permite usar as suas habilidades ou talentos?", "rev": False, "options": escala_freq},
                    {"id": "c16", "q": "No seu local de trabalho, você é informado com antecedência sobre decisões importantes ou mudanças?", "rev": False, "options": escala_freq},
                    {"id": "c17", "q": "Recebe toda a informação que necessita para fazer bem o seu trabalho?", "rev": False, "options": escala_freq}
                ],
                "Transparência de Papel e Conflitos": [
                    {"id": "c18", "q": "Seu trabalho apresenta objetivos claros?", "rev": False, "options": escala_freq},
                    {"id": "c19", "q": "Sabe exatamente quais são as suas responsabilidades?", "rev": False, "options": escala_freq},
                    {"id": "c20", "q": "Sabe exatamente o que é esperado de você?", "rev": False, "options": escala_freq},
                    {"id": "c21", "q": "O seu trabalho é reconhecido e apreciado pela gerência?", "rev": False, "options": escala_freq},
                    {"id": "c22", "q": "A gerência do seu local de trabalho respeita você?", "rev": False, "options": escala_freq},
                    {"id": "c23", "q": "Você é tratado de forma justa no seu local de trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c24", "q": "Faz coisas no seu trabalho que uns concordam mas outros não?", "rev": True, "options": escala_freq},
                    {"id": "c25", "q": "Por vezes tem que fazer coisas que deveriam ser feitas de outra maneira?", "rev": True, "options": escala_freq},
                    {"id": "c26", "q": "Por vezes tem que fazer coisas que considera desnecessárias?", "rev": True, "options": escala_freq}
                ],
                "Relações Sociais e Liderança": [
                    {"id": "c27", "q": "Com que frequência tem ajuda e apoio dos seus colegas de trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c28", "q": "Com que frequência os seus colegas estão dispostos a ouvi-lo(a) sobre os seus problemas de trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c29", "q": "Com que frequência os seus colegas conversam com você sobre o seu desempenho?", "rev": False, "options": escala_freq},
                    {"id": "c30", "q": "Com que frequência o seu superior imediato conversa com você sobre como está o andamento do seu trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c31", "q": "Com que frequência tem ajuda e apoio do seu superior imediato?", "rev": False, "options": escala_freq},
                    {"id": "c32", "q": "Com que frequência o seu superior imediato conversa com você em relação ao seu desempenho?", "rev": False, "options": escala_freq},
                    {"id": "c33", "q": "Existe um bom ambiente de trabalho entre você e os seus colegas?", "rev": False, "options": escala_freq},
                    {"id": "c34", "q": "Existe uma boa cooperação entre os colegas de trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c35", "q": "No seu local de trabalho você sente que faz parte de uma comunidade?", "rev": False, "options": escala_freq},
                    {"id": "c36", "q": "Sua chefia oferece para as pessoas e para a equipe boas oportunidades de desenvolvimento?", "rev": False, "options": escala_freq},
                    {"id": "c37", "q": "Sua chefia dá prioridade à satisfação no trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c38", "q": "Sua chefia é boa no planejamento do trabalho?", "rev": False, "options": escala_freq},
                    {"id": "c39", "q": "Sua chefia é boa em resolver conflitos?", "rev": False, "options": escala_freq}
                ],
                "Valores, Justiça e Confiança": [
                    {"id": "c40", "q": "Os colaboradores ocultam informações uns dos outros?", "rev": True, "options": escala_freq},
                    {"id": "c41", "q": "Os colaboradores ocultam informações da gerência?", "rev": True, "options": escala_freq},
                    {"id": "c42", "q": "Os colaboradores confiam uns nos outros de um modo geral?", "rev": False, "options": escala_freq},
                    {"id": "c43", "q": "A gerência confia nos colaboradores para fazerem o trabalho bem feito?", "rev": False, "options": escala_freq},
                    {"id": "c44", "q": "Você confia na informação que é transmitida pela gerência?", "rev": False, "options": escala_freq},
                    {"id": "c45", "q": "A gerência oculta informação aos seus colaboradores?", "rev": True, "options": escala_freq},
                    {"id": "c46", "q": "Os conflitos são resolvidos de uma forma justa?", "rev": False, "options": escala_freq},
                    {"id": "c47", "q": "As sugestões dos colaboradores são tratadas de forma séria pela gerência?", "rev": False, "options": escala_freq},
                    {"id": "c48", "q": "O trabalho é igualmente distribuído pelos colaboradores?", "rev": False, "options": escala_freq}
                ],
                "Atitude e Satisfação": [
                    {"id": "c49", "q": "Sou sempre capaz de resolver problemas, se tentar o suficiente.", "rev": False, "options": escala_int},
                    {"id": "c50", "q": "É fácil para mim seguir os meus planos e atingir os meus objetivos.", "rev": False, "options": escala_int},
                    {"id": "c51", "q": "O seu trabalho tem algum significado para você?", "rev": False, "options": escala_int},
                    {"id": "c52", "q": "Você sente que o seu trabalho é importante?", "rev": False, "options": escala_int},
                    {"id": "c53", "q": "Sente-se motivado e envolvido com o seu trabalho?", "rev": False, "options": escala_int},
                    {"id": "c54", "q": "Você gosta de falar com outras pessoas sobre o seu local de trabalho?", "rev": False, "options": escala_int},
                    {"id": "c55", "q": "Você sente que os problemas do seu local de trabalho também são seus?", "rev": False, "options": escala_int},
                    {"id": "c56", "q": "Em relação ao seu trabalho, quão satisfeito você está com as suas perspectivas profissionais?", "rev": False, "options": escala_sat},
                    {"id": "c57", "q": "Em relação ao seu trabalho, quão satisfeito você está com as condições físicas do seu local de trabalho?", "rev": False, "options": escala_sat},
                    {"id": "c58", "q": "Em relação ao seu trabalho, quão satisfeito você está com a forma como as suas capacidades são utilizadas?", "rev": False, "options": escala_sat},
                    {"id": "c59", "q": "Quão satisfeito você está com o seu trabalho de uma forma global?", "rev": False, "options": escala_sat},
                    {"id": "c60", "q": "Você se preocupa em ficar desempregado?", "rev": True, "options": escala_int}
                ],
                "Saúde, Bem-estar e Rotina": [
                    {"id": "c61", "q": "Em geral, você sente que a sua saúde é:", "rev": False, "options": escala_sau},
                    {"id": "c62", "q": "Sente que o seu trabalho exige muita energia que acaba por afetar a sua vida privada negativamente?", "rev": True, "options": escala_int},
                    {"id": "c63", "q": "Sente que o seu trabalho exige muito tempo que acaba por afetar a sua vida privada negativamente?", "rev": True, "options": escala_int},
                    {"id": "c64", "q": "Sua família e amigos dizem que você trabalha demais?", "rev": True, "options": escala_int},
                    {"id": "c65", "q": "Com que frequência nas últimas 4 semanas você sentiu dificuldade para adormecer?", "rev": True, "options": escala_freq},
                    {"id": "c66", "q": "Com que frequência nas últimas 4 semanas você acordou várias vezes durante a noite e depois não conseguia adormecer?", "rev": True, "options": escala_freq},
                    {"id": "c67", "q": "Com que frequência nas últimas 4 semanas você sentiu-se fisicamente exausto?", "rev": True, "options": escala_freq},
                    {"id": "c68", "q": "Com que frequência nas últimas 4 semanas você sentiu-se emocionalmente exausto?", "rev": True, "options": escala_freq},
                    {"id": "c69", "q": "Com que frequência nas últimas 4 semanas você sentiu-se irritado?", "rev": True, "options": escala_freq},
                    {"id": "c70", "q": "Com que frequência nas últimas 4 semanas você sentiu-se ansioso?", "rev": True, "options": escala_freq},
                    {"id": "c71", "q": "Com que frequência nas últimas 4 semanas você sentiu-se triste?", "rev": True, "options": escala_freq},
                    {"id": "c72", "q": "Com que frequência nas últimas 4 semanas você sentiu falta de interesse pelas coisas do dia a dia?", "rev": True, "options": escala_freq}
                ],
                "Ambiente Ofensivo (Últimos 12 meses)": [
                    {"id": "c73", "q": "Tem sido alvo de insultos ou provocações verbais no trabalho?", "rev": True, "options": escala_freq},
                    {"id": "c74", "q": "Tem sido exposto a assédio sexual indesejado?", "rev": True, "options": escala_freq},
                    {"id": "c75", "q": "Tem sido exposto a ameaças de violência?", "rev": True, "options": escala_freq},
                    {"id": "c76", "q": "Tem sido exposto a agressão física?", "rev": True, "options": escala_freq}
                ]
            }
        }
    }

# ==============================================================================
# 4. FUNÇÕES DO SISTEMA (CÁLCULOS E DADOS)
# ==============================================================================
def get_logo_html(width=180):
    if st.session_state.platform_config['logo_b64']:
        clean_b64 = st.session_state.platform_config['logo_b64']
        if clean_b64.startswith('data:image'):
            clean_b64 = clean_b64.split(',')[1]
        return f'<img src="data:image/png;base64,{clean_b64}" width="{width}" style="max-width: 100%; height: auto;">'
    
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
    try: 
        if file is not None:
            bytes_data = file.getvalue()
            return base64.b64encode(bytes_data).decode('utf-8')
        return None
    except Exception as e: 
        return None

def logout(): 
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.admin_permission = None
    st.rerun()

def get_copy_button_html(text_to_copy, button_label="📋 Copiar"):
    """Cria um botão HTML/JS elegante e nativo para copiar texto diretamente do Streamlit"""
    safe_text = json.dumps(text_to_copy)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{ margin: 0; padding: 0; background-color: transparent; font-family: 'Inter', sans-serif; }}
    .btn {{
        background-color: {COR_PRIMARIA};
        color: #ffffff;
        border: none;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
    }}
    .btn:hover {{
        background-color: {COR_SECUNDARIA};
        color: {COR_PRIMARIA};
    }}
    .btn.copied {{
        background-color: {COR_RISCO_BAIXO};
        color: #ffffff;
    }}
    </style>
    </head>
    <body>
        <button id="copy-btn" class="btn" onclick='copyAction()'>
            {button_label}
        </button>
        <script>
            function copyAction() {{
                const text = {safe_text};
                const el = document.createElement('textarea');
                el.value = text;
                document.body.appendChild(el);
                el.select();
                document.execCommand('copy');
                document.body.removeChild(el);
                
                const btn = document.getElementById('copy-btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Copiado com sucesso!';
                btn.classList.add('copied');
                
                setTimeout(() => {{
                    btn.innerHTML = originalText;
                    btn.classList.remove('copied');
                }}, 2500);
            }}
        </script>
    </body>
    </html>
    """
    return html

def calculate_actual_scores(all_responses, companies_list, methodologies_dict):
    comp_method_map = {str(c['id']): c.get('metodologia', 'HSE-IT (35 itens)') for c in companies_list}
    
    # Engine matemático de match exato para converter strings nas pontuações de 1 a 5
    scale_1 = ["Nunca/Quase Nunca", "Nada/Quase Nada", "Muito Insatisfeito", "Deficitária", "Discordo Totalmente"]
    scale_2 = ["Raramente", "Um pouco", "Insatisfeito", "Razoável", "Discordo"]
    scale_3 = ["Às vezes", "Moderadamente", "Neutro", "Boa"]
    scale_4 = ["Frequentemente", "Muito", "Satisfeito", "Muito Boa", "Concordo"]
    scale_5 = ["Sempre", "Extremamente", "Muito Satisfeito", "Excelente", "Concordo Totalmente"]
    
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
                    if user_ans in scale_1: val = 5 if is_rev else 1
                    elif user_ans in scale_2: val = 4 if is_rev else 2
                    elif user_ans in scale_3: val = 3 
                    elif user_ans in scale_4: val = 2 if is_rev else 4
                    elif user_ans in scale_5: val = 1 if is_rev else 5

                    if val is not None:
                        total_score += val
                        count_valid += 1
                        
        resp_row['score_calculado'] = round(total_score / count_valid, 2) if count_valid > 0 else 0
    
    return all_responses

def process_company_analytics(comp, comp_resps, active_questions):
    comp['respondidas'] = len(comp_resps)
    
    if comp['respondidas'] == 0:
        comp['score'] = 0.0
        comp['dimensoes'] = {cat: 0.0 for cat in active_questions.keys()}
        comp['detalhe_perguntas'] = {}
        return comp

    dimensoes_totais = {cat: [] for cat in active_questions.keys()}
    soma_por_pergunta = {} 
    total_por_pergunta = {}
    
    scale_1 = ["Nunca/Quase Nunca", "Nada/Quase Nada", "Muito Insatisfeito", "Deficitária", "Discordo Totalmente"]
    scale_2 = ["Raramente", "Um pouco", "Insatisfeito", "Razoável", "Discordo"]
    scale_3 = ["Às vezes", "Moderadamente", "Neutro", "Boa"]
    scale_4 = ["Frequentemente", "Muito", "Satisfeito", "Muito Boa", "Concordo"]
    scale_5 = ["Sempre", "Extremamente", "Muito Satisfeito", "Excelente", "Concordo Totalmente"]

    for resp_row in comp_resps:
        ans_dict = resp_row.get('answers', {})
        
        for cat, qs in active_questions.items():
            for q in qs:
                q_text = q['q']
                is_rev = q.get('rev', False)
                user_ans = ans_dict.get(q_text)
                
                if user_ans:
                    val = None
                    if user_ans in scale_1: val = 5 if is_rev else 1
                    elif user_ans in scale_2: val = 4 if is_rev else 2
                    elif user_ans in scale_3: val = 3 
                    elif user_ans in scale_4: val = 2 if is_rev else 4
                    elif user_ans in scale_5: val = 1 if is_rev else 5

                    if val is not None:
                        dimensoes_totais[cat].append(val)
                        if q_text not in soma_por_pergunta:
                            soma_por_pergunta[q_text] = 0
                            total_por_pergunta[q_text] = 0
                            
                        total_por_pergunta[q_text] += 1
                        soma_por_pergunta[q_text] += val

    dim_averages = {}
    for cat, vals in dimensoes_totais.items():
        dim_averages[cat] = round(sum(vals) / len(vals), 1) if vals else 0.0

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
    all_answers = []
    companies = []
    
    if DB_CONNECTED:
        try:
            companies = supabase.table('companies').select("*").execute().data
            all_answers = supabase.table('responses').select("*").execute().data
            
            users_raw = supabase.table('admin_users').select("*").execute().data
            if users_raw:
                st.session_state.users_db = {u['username']: u for u in users_raw}
        except Exception as e:
            pass
            
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
    history_dict = {}
    
    for r in all_responses:
        if str(r.get('company_id')) != str(comp_id): 
            continue
        
        created_at = r.get('created_at')
        if not created_at: 
            periodo = "Lote Anterior"
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
    if DB_CONNECTED:
        try:
            supabase.table('responses').delete().eq('company_id', comp_id).execute()
            supabase.table('admin_users').delete().eq('linked_company_id', comp_id).execute()
            supabase.table('companies').delete().eq('id', comp_id).execute()
        except Exception as e: 
            st.warning(f"Não foi possível remover no momento: {e}")
            return
    
    st.session_state.companies_db = [c for c in st.session_state.companies_db if str(c['id']) != str(comp_id)]
    st.success("✅ O Cliente e todos os dados associados foram removidos com sucesso.")
    time.sleep(1.5)
    st.rerun()

def delete_user(username):
    if DB_CONNECTED:
        try:
            supabase.table('admin_users').delete().eq('username', username).execute()
        except Exception as e: 
            st.error(f"Erro ao remover: {e}")
    
    if username in st.session_state.users_db:
        del st.session_state.users_db[username]
    
    st.success(f"✅ O usuário [{username}] foi removido com sucesso!")
    time.sleep(1)
    st.rerun()

def kpi_card(title, value, icon, color_class):
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
    riscos = [k for k, v in dimensoes.items() if v < 3.0 and v > 0]
    texto = "O presente diagnóstico mapeou os principais indicadores de saúde e bem-estar no ambiente de trabalho da equipe. A avaliação foi baseada em rigorosas metodologias de saúde ocupacional. "
    
    if riscos:
        texto += f"A análise revela que os fatores associados a **{', '.join(riscos)}** requerem atenção especial por parte da liderança, pois apresentam resultados abaixo do recomendável (Score Inferior a 3.0). Quando não gerenciados adequadamente, estes fatores podem contribuir para o aumento do estresse, desgaste emocional e rotatividade na equipe. "
    else:
        texto += "Os resultados indicam um ambiente de trabalho globalmente saudável, equilibrado e com bons níveis de proteção e bem-estar. As métricas avaliadas encontram-se dentro de parâmetros muito positivos. "
    
    texto += "Recomendamos que as lideranças e a equipe de RH analisem as ações propostas a seguir, procurando aplicar melhorias contínuas para fortalecer ainda mais o clima organizacional."
    return texto

def gerar_banco_sugestoes(dimensoes):
    sugestoes = []
    
    # ------------------ BLOCO 1: EXIGÊNCIAS, CARGA E RITMO DE TRABALHO ------------------
    if dimensoes.get("Demandas", 5) < 3.8 or dimensoes.get("Exigências Laborais (Quantidade e Ritmo)", 5) < 3.8:
        sugestoes.append({
            "acao": "Avaliação Ergonômica e Cognitiva da Carga de Trabalho", 
            "estrat": "Analisar profundamente as rotinas para identificar sobrecargas invisíveis (trabalho cognitivo e emocional intenso), tarefas duplicadas e otimizar a distribuição do trabalho na base.", 
            "area": "Gestão de Demandas", "resp": "Coordenação de Área", "prazo": "30 a 60 dias"
        })
        sugestoes.append({
            "acao": "Matriz de Prioridades e Redução de Urgências", 
            "estrat": "Treinar as equipes a organizar melhor o tempo e blindar os colaboradores contra a cultura da urgência, evitando o desgaste contínuo e combatendo 'incêndios diários'.", 
            "area": "Gestão de Demandas", "resp": "Líderes de Equipe", "prazo": "15 dias"
        })
        sugestoes.append({
            "acao": "Política de Desconexão Digital", 
            "estrat": "Criar combinados claros com a equipe sobre o respeito absoluto aos horários de descanso, evitando e-mails e mensagens de trabalho fora do expediente contratual.", 
            "area": "Gestão de Demandas", "resp": "Recursos Humanos", "prazo": "30 dias"
        })
        sugestoes.append({
            "acao": "Rodízio de Tarefas de Alto Desgaste Emocional", 
            "estrat": "Implementar um sistema de revezamento para colaboradores que lidam constantemente com clientes difíceis ou situações de alta carga emocional, evitando a fadiga e o cinismo.", 
            "area": "Design do Trabalho", "resp": "Coordenação Operacional", "prazo": "Contínuo"
        })
        sugestoes.append({
            "acao": "Pausas Estratégicas Obrigatórias", 
            "estrat": "Institucionalizar micropausas de descompressão cognitiva entre blocos intensos de concentração, melhorando a preservação mental da equipe (ex: Técnica Pomodoro aplicada).", 
            "area": "Saúde Ocupacional", "resp": "SESMT / Liderança", "prazo": "Imediato"
        })
        
    # ------------------ BLOCO 2: AUTONOMIA, CONTROLE E INFLUÊNCIA ------------------
    if dimensoes.get("Controle", 5) < 3.8 or dimensoes.get("Organização e Influência", 5) < 3.8:
        sugestoes.append({
            "acao": "Job Crafting (Redesenho do Trabalho)", 
            "estrat": "Autorizar e estimular que o profissional tenha autonomia para remodelar de forma positiva a maneira como executa suas tarefas diárias, respeitando sua forma de produzir.", 
            "area": "Autonomia e Organização", "resp": "Gestão Direta", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Gestão Focada em Entregas (Resultados vs. Horas)", 
            "estrat": "Migrar o foco da avaliação baseada em presencialismo (horas em tela) para a qualidade das entregas, fomentando maior responsabilidade e flexibilidade de tempo.", 
            "area": "Autonomia e Organização", "resp": "Diretoria e Lideranças", "prazo": "Trimestral"
        })
        sugestoes.append({
            "acao": "Comitês de Escuta Ativa para Decisões", 
            "estrat": "Envolver os profissionais da base em pequenas rodadas de escuta ANTES de tomar decisões top-down sobre softwares, rotinas ou mudanças no ambiente físico.", 
            "area": "Autonomia e Organização", "resp": "Líderes de Setor", "prazo": "Ad Hoc"
        })
        sugestoes.append({
            "acao": "Programa de Aproveitamento de Talentos", 
            "estrat": "Mapear habilidades subutilizadas na equipe e criar projetos especiais onde o colaborador possa usar todo seu potencial criativo e técnico.", 
            "area": "Desenvolvimento", "resp": "T&D (Treinamento)", "prazo": "Plano Anual"
        })
        
    # ------------------ BLOCO 3: SUPORTE, LIDERANÇA E RELAÇÕES SOCIAIS ------------------
    if dimensoes.get("Suporte do Gestor", 5) < 3.8 or dimensoes.get("Suporte dos Colegas", 5) < 3.8 or dimensoes.get("Relações Sociais e Liderança", 5) < 3.8:
        sugestoes.append({
            "acao": "Letramento em Liderança Empática e Sensível", 
            "estrat": "Treinar intensivamente toda a camada de gestão em Inteligência Emocional, Comunicação Não-Violenta (CNV) e condução de equipes com segurança psicológica.", 
            "area": "Liderança", "resp": "Pessin Gestão / RH", "prazo": "90 dias"
        })
        sugestoes.append({
            "acao": "Reuniões de Check-in (1:1) Focadas no Humano", 
            "estrat": "Implementar agendas inegociáveis de 1:1 focadas não nas metas da semana, mas em ouvir as dores, a carreira e o bem-estar genuíno do colaborador.", 
            "area": "Liderança", "resp": "Gestão Direta", "prazo": "Ação Contínua"
        })
        sugestoes.append({
            "acao": "Cultura Constante de Reconhecimento Positivo", 
            "estrat": "Criar um fórum de elogios abertos ou plataformas onde líderes e colegas valorizam publicamente pequenas vitórias, destruindo a cultura de 'apontar só os erros'.", 
            "area": "Clima", "resp": "Recursos Humanos", "prazo": "Imediato"
        })
        sugestoes.append({
            "acao": "Programa de Mentoria Institucional (Buddy)", 
            "estrat": "Designar 'padrinhos' veteranos e acolhedores para acompanhar de perto cada novo colaborador nos primeiros 90 dias, reduzindo a sensação de solidão organizacional.", 
            "area": "Clima e Acolhimento", "resp": "Recursos Humanos", "prazo": "30 dias"
        })
        sugestoes.append({
            "acao": "Dinâmicas de Fortalecimento de Equipe (Team Building)", 
            "estrat": "Investir em rituais leves e de descompressão fora do ambiente estrito de trabalho para fortalecer os laços de comunidade, pertencimento e confiança interpessoal.", 
            "area": "Clima", "resp": "Comunicação Interna", "prazo": "Semestral"
        })

    # ------------------ BLOCO 4: AMBIENTE, RESPEITO E GESTÃO DE CONFLITOS ------------------
    if dimensoes.get("Relacionamentos", 5) < 3.8 or dimensoes.get("Ambiente Ofensivo (Últimos 12 meses)", 5) < 3.8 or dimensoes.get("Transparência de Papel e Conflitos", 5) < 3.8:
        sugestoes.append({
            "acao": "Política de Tolerância Zero (Assédio e Discriminação)", 
            "estrat": "Oficializar e divulgar agressivamente um código de conduta inquebrável contra bullying, assédio moral, exclusões ou palavras ofensivas, com consequências rígidas.", 
            "area": "Compliance e Clima", "resp": "Diretoria e Jurídico", "prazo": "Imediato"
        })
        sugestoes.append({
            "acao": "Canal de Ouvidoria Anônimo e Independente", 
            "estrat": "Contratar ou disponibilizar uma plataforma terceira 100% blindada para o reporte seguro de assédio ou liderança abusiva, garantindo total ausência de retaliação.", 
            "area": "Compliance", "resp": "RH Estratégico", "prazo": "60 dias"
        })
        sugestoes.append({
            "acao": "Mediação Profissional de Conflitos Internos", 
            "estrat": "Frente à identificação de setores 'tóxicos', intervir cirurgicamente com especialistas em mediação de conflito para desfazer panelinhas e resolver quebras de relação.", 
            "area": "Clima", "resp": "Pessin Gestão / RH", "prazo": "Sob Demanda"
        })
        
    # ------------------ BLOCO 5: PROPÓSITO, VALORES, JUSTIÇA E SATISFAÇÃO ------------------
    if dimensoes.get("Papel na Empresa", 5) < 3.8 or dimensoes.get("Valores, Justiça e Confiança", 5) < 3.8 or dimensoes.get("Atitude e Satisfação", 5) < 3.8:
        sugestoes.append({
            "acao": "Alinhamento Claro de Funções (Job Description Vivo)", 
            "estrat": "Acabar com as zonas cinzentas de responsabilidade. Documentar e assinar junto com o time o que exatamente é (e o que não é) tarefa daquela posição.", 
            "area": "Organização", "resp": "Gestores de Área", "prazo": "60 dias"
        })
        sugestoes.append({
            "acao": "Cascateamento de Propósito e Visão", 
            "estrat": "Liderança de topo deve descer à operação para mostrar, com exemplos claros, como o aperto de um parafuso ou o envio de um e-mail base impacta a vida do cliente final.", 
            "area": "Sentido do Trabalho", "resp": "Direção Executiva", "prazo": "Trimestral"
        })
        sugestoes.append({
            "acao": "Transparência em Critérios de Promoção e Mérito", 
            "estrat": "Aumentar a justiça organizacional divulgando abertamente o que é necessário realizar (PDI, metas) para ascender na empresa, evitando promoções percebidas como favoritismo.", 
            "area": "Justiça e Cultura", "resp": "Recursos Humanos", "prazo": "Plano Anual"
        })
        sugestoes.append({
            "acao": "Fórum de Transparência da Diretoria", 
            "estrat": "Criar um espaço (Town Hall) onde a gerência abre o jogo sobre as dificuldades, rumos e sucessos da empresa, reduzindo a sensação de que 'escondem informações'.", 
            "area": "Confiança", "resp": "Diretoria", "prazo": "Semestral"
        })
        
    # ------------------ BLOCO 6: GESTÃO E TRANSIÇÃO DE MUDANÇAS ------------------
    if dimensoes.get("Gestão de Mudança", 5) < 3.8:
        sugestoes.append({
            "acao": "Comunicação Antecipada e Transparente", 
            "estrat": "Nunca surpreender o time com mudanças que afetam sua rotina. Explicar sempre o 'porquê' da alteração com semanas de antecedência, mitigando a ansiedade natural.", 
            "area": "Gestão de Mudança", "resp": "Comunicação Interna", "prazo": "Por Projeto"
        })
        sugestoes.append({
            "acao": "Comitê de Embaixadores da Mudança", 
            "estrat": "Identificar formadores de opinião na operação para testarem novos sistemas primeiro e atuarem como multiplicadores de segurança para os colegas mais resistentes.", 
            "area": "Gestão de Mudança", "resp": "Líder de Projetos", "prazo": "Por Projeto"
        })

    # ------------------ BLOCO 7: SAÚDE, BEM-ESTAR, SONO E FAMÍLIA (EXCLUSIVO COPSOQ) ------------------
    if dimensoes.get("Saúde, Bem-estar e Rotina", 5) < 3.8:
        sugestoes.append({
            "acao": "Programa Estruturado de Apoio Psicológico", 
            "estrat": "Firmar parcerias com plataformas terapêuticas subsidiando sessões de psicoterapia, com foco urgente no combate aos altos índices de ansiedade e exaustão emocional.", 
            "area": "Saúde Mental", "resp": "Benefícios / SESMT", "prazo": "Ação Imediata"
        })
        sugestoes.append({
            "acao": "Workshops de Higiene do Sono e Prevenção ao Burnout", 
            "estrat": "Trazer profissionais de saúde para ensinar o colaborador a 'desligar' o cérebro à noite e reconhecer em si e nos colegas os sinais precoces da estafa.", 
            "area": "Saúde Ocupacional", "resp": "T&D e SESMT", "prazo": "Trimestral"
        })
        sugestoes.append({
            "acao": "Políticas Reais de Flexibilidade Familiar", 
            "estrat": "Apoiar mães/pais na conciliação familiar com horários híbridos reais, auxílio-creche estruturado e respeito a emergências familiares, reduzindo a culpa do trabalhador.", 
            "area": "Bem-estar (Work-life)", "resp": "RH Institucional", "prazo": "Revisão Anual"
        })
        
    # ------------------ FALLBACK (CENÁRIO EXCELENTE) ------------------
    if not sugestoes:
        sugestoes.append({
            "acao": "Monitoramento Contínuo com Pesquisas de Pulso", 
            "estrat": "Não relaxar o acompanhamento. Manter questionários semanais de 3 perguntas na intranet para identificar qualquer micro-fissura no clima rapidamente.", 
            "area": "Estratégia Geral", "resp": "Recursos Humanos", "prazo": "Contínuo"
        })
        sugestoes.append({
            "acao": "Pacote Avançado de Qualidade de Vida", 
            "estrat": "Sustentar a boa saúde mental com iniciativas premium: Gympass ativo, massagem rápida, snacks saudáveis, palestras de educação financeira e bem-estar geral.", 
            "area": "Estratégia Geral", "resp": "Recursos Humanos", "prazo": "Contínuo"
        })
        
    return sugestoes

# ==============================================================================
# 5. MÓDULO DE TELAS E FLUXOS DA LIDERANÇA / RH
# ==============================================================================

def login_screen():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'>{get_logo_html(250)}</div>", unsafe_allow_html=True)
        plat_name = st.session_state.platform_config.get('name', 'Sistema')
        st.markdown(f"<h3 style='text-align:center; color:#555;'>Bem-vindo(a) ao {plat_name}</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:gray;'>Acesso exclusivo para Gestores e Consultores</p>", unsafe_allow_html=True)
        
        with st.form("login"):
            user = st.text_input("Seu Usuário de Acesso")
            pwd = st.text_input("Sua Senha", type="password")
            
            if st.form_submit_button("Acessar o Painel", type="primary", use_container_width=True):
                login_ok = False
                user_role_type = "Analista"
                user_credits = 0
                linked_comp = None
                
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
                
                if not login_ok and user in st.session_state.users_db and st.session_state.users_db[user].get('password') == pwd:
                    login_ok = True
                    user_data = st.session_state.users_db[user]
                    user_role_type = user_data.get('role', 'Analista')
                    user_credits = user_data.get('credits', 0)
                    linked_comp = user_data.get('linked_company_id')
                
                if login_ok:
                    valid_until = user_data.get('valid_until')
                    if valid_until and datetime.datetime.today().isoformat() > valid_until:
                        st.error("🔒 O seu acesso atingiu a data de validade. Por favor, fale conosco para renovar.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_role = 'admin'
                        
                        if user == 'admin':
                            user_role_type = 'Master'
                            user_credits = 999999
                        
                        st.session_state.admin_permission = user_role_type 
                        st.session_state.user_username = user
                        st.session_state.user_credits = user_credits
                        st.session_state.user_linked_company = linked_comp
                        
                        st.rerun()
                else: 
                    st.error("⚠️ Não conseguimos encontrar este usuário ou a senha está incorreta. Tente novamente.")
                    

def admin_dashboard():
    companies_data, responses_data = load_data_from_db()
    
    perm = st.session_state.admin_permission
    curr_user = st.session_state.user_username
    
    if perm == "Gestor":
        visible_companies = [c for c in companies_data if c.get('owner') == curr_user]
    elif perm == "Analista":
        linked_id = st.session_state.user_linked_company
        visible_companies = [c for c in companies_data if c['id'] == linked_id]
    else: 
        visible_companies = companies_data

    total_used_by_user = sum(c.get('respondidas', 0) for c in visible_companies) if perm != "Analista" else (visible_companies[0].get('respondidas', 0) if visible_companies else 0)
    credits_left = st.session_state.user_credits - total_used_by_user

    menu_options = ["Visão Geral", "Links de Pesquisa", "Relatórios e Laudos", "Histórico de Evolução"]
    if perm in ["Master", "Gestor"]:
        menu_options.insert(1, "Clientes (Empresas)")
        menu_options.insert(2, "Setores e Cargos")
    if perm == "Master":
        menu_options.append("Configurações")

    icons_map = {
        "Visão Geral": "grid", 
        "Clientes (Empresas)": "building", 
        "Setores e Cargos": "list-task", 
        "Links de Pesquisa": "link-45deg", 
        "Relatórios e Laudos": "file-text", 
        "Histórico de Evolução": "clock-history", 
        "Configurações": "gear"
    }

    with st.sidebar:
        st.markdown(f"<div style='text-align:center; margin-bottom:30px; margin-top:20px;'>{get_logo_html(160)}</div>", unsafe_allow_html=True)
        st.caption(f"Bem-vindo(a), **{curr_user}** <br> Perfil: **{perm}**", unsafe_allow_html=True)
        
        if perm != "Master":
            st.info(f"💳 Avaliações Disponíveis: {credits_left}")

        selected = option_menu(
            menu_title=None, 
            options=menu_options, 
            icons=[icons_map[o] for o in menu_options], 
            default_index=0, 
            styles={"nav-link-selected": {"background-color": COR_PRIMARIA}}
        )
        st.markdown("---")
        if st.button("🚪 Sair com Segurança", use_container_width=True): 
            logout()

    if selected == "Visão Geral":
        st.title("Visão Geral do Sistema")
        
        lista_empresas_filtro = ["Todas as Empresas"] + [c['razao'] for c in visible_companies]
        empresa_filtro = st.selectbox("Selecione os dados que deseja visualizar:", lista_empresas_filtro)
        
        if empresa_filtro != "Todas as Empresas":
            companies_filtered = [c for c in visible_companies if c['razao'] == empresa_filtro]
            target_id = companies_filtered[0]['id']
            responses_filtered = [r for r in responses_data if str(r['company_id']) == str(target_id)]
        else:
            companies_filtered = visible_companies
            ids_visiveis = [str(c['id']) for c in visible_companies]
            responses_filtered = [r for r in responses_data if str(r['company_id']) in ids_visiveis]

        total_resp_view = len(responses_filtered)
        total_vidas_view = sum(c.get('func', 0) for c in companies_filtered)
        
        col1, col2, col3, col4 = st.columns(4)
        if perm == "Analista":
            with col1: kpi_card("Total de Colaboradores", total_vidas_view, "👥", "bg-blue")
            with col2: kpi_card("Respostas Recebidas", total_resp_view, "✅", "bg-green")
            with col3: kpi_card("Avaliações Disponíveis", credits_left, "💳", "bg-orange") 
        else:
            with col1: kpi_card("Empresas Ativas", len(companies_filtered), "🏢", "bg-blue")
            with col2: kpi_card("Respostas Recebidas", total_resp_view, "✅", "bg-green")
            if perm == "Master": 
                with col3: kpi_card("Total de Vidas Mapeadas", total_vidas_view, "👥", "bg-orange") 
            else: 
                with col3: kpi_card("Avaliações Disponíveis", credits_left, "💳", "bg-orange")

        with col4: kpi_card("Alertas de Risco", 0, "🚨", "bg-red")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### Média Geral por Dimensão (Radar)")
            
            if companies_filtered and total_resp_view > 0:
                metodo_predominante = companies_filtered[0].get('metodologia', 'HSE-IT (35 itens)')
                comps_validas = [c for c in companies_filtered if c.get('metodologia', 'HSE-IT (35 itens)') == metodo_predominante]
                categories = list(st.session_state.methodologies[metodo_predominante]['questions'].keys())
                
                avg_dims = {cat: 0 for cat in categories}
                count_comps_with_data = 0
                
                for c in comps_validas:
                    if c.get('respondidas', 0) > 0:
                        count_comps_with_data += 1
                        for cat in categories: 
                            avg_dims[cat] += c['dimensoes'].get(cat, 0)
                
                valores_radar = [round(avg_dims[cat]/count_comps_with_data, 1) for cat in categories] if count_comps_with_data > 0 else [0]*len(categories)

                fig_radar = go.Figure(go.Scatterpolar(r=valores_radar, theta=categories, fill='toself', name='Média Global', line_color=COR_SECUNDARIA))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=300, margin=dict(t=20, b=20))
                st.plotly_chart(fig_radar, use_container_width=True)
                st.caption(f"Metodologia Ativa: **{metodo_predominante}**")
            else: 
                st.info("Aguardando novas respostas para gerar o gráfico.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### Média de Saúde Ocupacional por Setor")
            if responses_filtered:
                df_resp = pd.DataFrame(responses_filtered)
                
                if 'setor' in df_resp.columns and 'score_calculado' in df_resp.columns:
                    df_setor = df_resp.groupby('setor')['score_calculado'].mean().reset_index()
                    fig_bar = px.bar(
                        df_setor, 
                        x='setor', 
                        y='score_calculado', 
                        title="Comparativo entre Áreas", 
                        color='score_calculado', 
                        color_continuous_scale='RdYlGn', 
                        range_y=[0, 5]
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else: 
                    st.info("Sem dados suficientes de setores para processar.")
            else: 
                st.info("Aguardando as respostas dos colaboradores para formar o gráfico de barras.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        c3, c4 = st.columns([1.5, 1])
        with c3:
             st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
             st.markdown("##### Status das Avaliações (Adesão)")
             if companies_filtered:
                 status_dist = {"Pesquisa Concluída": 0, "Pesquisa em Andamento": 0}
                 for c in companies_filtered:
                     if c.get('respondidas',0) >= c.get('func',1): 
                         status_dist["Pesquisa Concluída"] += 1
                     else: 
                         status_dist["Pesquisa em Andamento"] += 1
                 
                 fig_pie = px.pie(names=list(status_dist.keys()), values=list(status_dist.values()), hole=0.6, color_discrete_sequence=[COR_SECUNDARIA, COR_RISCO_MEDIO])
                 fig_pie.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
                 st.plotly_chart(fig_pie, use_container_width=True)
             else: 
                 st.info("Cadastre uma empresa para visualizar este gráfico.")
             st.markdown("</div>", unsafe_allow_html=True)

    elif selected == "Clientes (Empresas)":
        st.title("Gestão de Clientes")
        
        if st.session_state.edit_mode:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.subheader("✏️ Editar os Dados do Cliente")
            target_id = st.session_state.edit_id
            emp_edit = next((c for c in visible_companies if c['id'] == target_id), None)
            
            if emp_edit:
                with st.form("edit_form"):
                    c1, c2, c3 = st.columns(3)
                    new_razao = c1.text_input("Razão Social", value=emp_edit['razao'])
                    new_cnpj = c2.text_input("CNPJ", value=emp_edit.get('cnpj',''))
                    new_cnae = c3.text_input("CNAE", value=emp_edit.get('cnae',''))
                    
                    c4, c5, c6 = st.columns(3)
                    risco_opts = [1, 2, 3, 4]
                    idx_risco = risco_opts.index(emp_edit.get('risco',1)) if emp_edit.get('risco',1) in risco_opts else 0
                    new_risco = c4.selectbox("Grau de Risco (1 a 4)", risco_opts, index=idx_risco)
                    new_func = c5.number_input("Número de Colaboradores (Vidas)", min_value=1, value=emp_edit.get('func',100))
                    new_limit = c6.number_input("Limite de Questionários (Cota)", min_value=1, value=emp_edit.get('limit_evals', 100))
                    
                    seg_opts = ["GHE", "Setor", "GES"]
                    idx_seg = seg_opts.index(emp_edit.get('segmentacao','GHE')) if emp_edit.get('segmentacao','GHE') in seg_opts else 0
                    new_seg = c6.selectbox("Tipo de Segmentação", seg_opts, index=idx_seg)
                    
                    c7, c8, c9 = st.columns(3)
                    new_resp = c7.text_input("Nome do Responsável (RH/Líder)", value=emp_edit.get('resp',''))
                    new_email = c8.text_input("E-mail do Responsável", value=emp_edit.get('email',''))
                    new_tel = c9.text_input("Telefone", value=emp_edit.get('telefone',''))
                    
                    new_end = st.text_input("Endereço Completo", value=emp_edit.get('endereco',''))
                    
                    val_atual = datetime.date.today() + datetime.timedelta(days=365)
                    if emp_edit.get('valid_until'):
                        try: val_atual = datetime.date.fromisoformat(emp_edit['valid_until'])
                        except: pass
                    new_valid = st.date_input("Validade do Link de Pesquisa:", value=val_atual)
                    
                    # Carrega a configuração atual de CPF da empresa (se houver, senao True)
                    current_cpf_req = emp_edit.get('org_structure', {}).get('_exigir_cpf', True) if isinstance(emp_edit.get('org_structure'), dict) else True
                    new_exigir_cpf = st.checkbox("🔒 Exigir CPF para evitar respostas duplicadas (Recomendado)", value=current_cpf_req)
                    
                    if st.form_submit_button("💾 Guardar Alterações", type="primary"):
                        updated_org = emp_edit.get('org_structure', {})
                        if not isinstance(updated_org, dict):
                            updated_org = {"Geral": ["Geral"]}
                        updated_org['_exigir_cpf'] = new_exigir_cpf
                        
                        update_dict = {
                            'razao': new_razao, 'cnpj': new_cnpj, 'cnae': new_cnae, 
                            'risco': new_risco, 'func': new_func, 'segmentacao': new_seg, 
                            'resp': new_resp, 'email': new_email, 'telefone': new_tel, 
                            'endereco': new_end, 'limit_evals': new_limit, 'valid_until': new_valid.isoformat(),
                            'org_structure': updated_org
                        }
                        
                        if DB_CONNECTED:
                            try: 
                                supabase.table('companies').update(update_dict).eq('id', target_id).execute()
                            except Exception as e: 
                                st.warning(f"Erro ao salvar na nuvem: {e}")
                        
                        emp_edit.update(update_dict)
                        st.session_state.edit_mode = False
                        st.session_state.edit_id = None
                        st.success("✅ Os dados do cliente foram atualizados com sucesso.")
                        time.sleep(1)
                        st.rerun()
                        
                if st.button("⬅️ Cancelar e Voltar"): 
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                st.error("Desculpe, perdemos a referência deste cliente. Por favor, atualize a página.")
        
        else:
            tab1, tab2 = st.tabs(["📋 Clientes Cadastrados", "➕ Cadastrar Novo Cliente"])
            with tab1:
                if not visible_companies: 
                    st.info("Ainda não existem clientes na sua lista. Comece a criar adicionando no botão acima.")
                
                for emp in visible_companies:
                    with st.expander(f"🏢 {emp['razao']}"):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.write(f"**CNPJ:** {emp.get('cnpj','')}")
                        c2.write(f"**Avaliações:** {emp.get('respondidas',0)} / {emp.get('limit_evals', '∞')}")
                        c3.info(f"**Metodologia:** {emp.get('metodologia', 'HSE-IT (35 itens)')}")
                        
                        c4_1, c4_2 = c4.columns(2)
                        if c4_1.button("✏️ Editar", key=f"ed_{emp['id']}"): 
                             st.session_state.edit_mode = True
                             st.session_state.edit_id = emp['id']
                             st.rerun()
                        
                        if perm == "Master":
                            if c4_2.button("🗑️ Remover", key=f"del_{emp['id']}"): 
                                delete_company(emp['id'])
            
            with tab2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                with st.form("add_comp_form_gigante"):
                    if credits_left <= 0 and perm != "Master":
                        st.error("🚫 O seu plano atingiu o limite de avaliações disponíveis. Fale conosco para adquirir mais.")
                        st.form_submit_button("Ação Bloqueada", disabled=True)
                    else:
                        st.write("### Dados da Empresa")
                        c1, c2, c3 = st.columns(3)
                        razao = c1.text_input("Razão Social")
                        cnpj = c2.text_input("CNPJ")
                        cnae = c3.text_input("CNAE")
                        
                        c4, c5, c6, c_met = st.columns(4)
                        risco = c4.selectbox("Grau de Risco (1 a 4)", [1,2,3,4])
                        func = c5.number_input("Número de Colaboradores (Vidas)", min_value=1)
                        limit_evals = c6.number_input("Limite de Questionários (Cota)", min_value=1, max_value=credits_left if perm!="Master" else 99999, value=min(100, credits_left if perm!="Master" else 100))
                        
                        metodologia_selecionada = c_met.selectbox("Metodologia de Avaliação", list(st.session_state.methodologies.keys()), help="Escolha qual a base de perguntas que fará sentido para a realidade deste cliente.")

                        st.write("### Dados de Contato e Acesso")
                        c7, c8, c9 = st.columns(3)
                        segmentacao = c7.selectbox("Tipo de Segmentação", ["GHE", "Setor", "GES"])
                        resp = c8.text_input("Nome do Responsável (RH/Líder)")
                        email = c9.text_input("E-mail do Responsável")
                        
                        c10, c11, c12 = st.columns(3)
                        tel = c10.text_input("Telefone")
                        valid_date = c11.date_input("Validade do Link de Pesquisa:", value=datetime.date.today() + datetime.timedelta(days=365))
                        c12.info("O sistema criará um link seguro automaticamente.")
                        
                        end = st.text_input("Endereço Completo")
                        logo_cliente = st.file_uploader("Logotipo do Cliente (Opcional - Formatos PNG ou JPG)", type=['png', 'jpg', 'jpeg'])
                        
                        st.markdown("---")
                        st.write("### Privacidade da Pesquisa")
                        exigir_cpf = st.checkbox("🔒 Exigir CPF do colaborador para evitar respostas duplicadas (O dado será criptografado no banco para garantir o anonimato)", value=True)
                        
                        st.markdown("---")
                        st.write("### Acesso Exclusivo para o Cliente (Portal do Analista)")
                        st.caption("Crie aqui um acesso para que a equipe de RH do cliente possa visualizar os seus próprios resultados e dashboards.")
                        u_login = st.text_input("Usuário de Acesso")
                        u_pass = st.text_input("Senha de Acesso", type="password")

                        if st.form_submit_button("✅ Salvar Cadastro e Gerar Link", type="primary"):
                            if not razao: 
                                st.error("⚠️ Preencha pelo menos a Razão Social da empresa para podermos avançar.")
                            else:
                                cod = str(uuid.uuid4())[:8].upper()
                                logo_str = image_to_base64(logo_cliente)
                                
                                org_structure_dict = {"Geral": ["Geral"], "_exigir_cpf": exigir_cpf}
                                
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
                                    "org_structure": org_structure_dict
                                }
                                
                                error_msg = None
                                if DB_CONNECTED:
                                    try:
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
                                    st.warning(f"⚠️ Atenção: Salvo apenas localmente devido a uma falha na internet: {error_msg}")
                                else: 
                                    st.success(f"🎉 Fantástico! O cliente foi cadastrado com sucesso.")
                                
                                time.sleep(2.5)
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    elif selected == "Setores e Cargos":
        st.title("Gestão de Setores e Cargos")
        if not visible_companies: 
            st.warning("⚠️ Precisa primeiro cadastrar um cliente antes de organizar os setores."); return
        
        empresa_nome = st.selectbox("Selecione a empresa para configurar os setores:", [c['razao'] for c in visible_companies])
        empresa = next((c for c in visible_companies if c['razao'] == empresa_nome), None)
        
        if empresa is not None:
            if 'org_structure' not in empresa or not isinstance(empresa['org_structure'], dict): 
                empresa['org_structure'] = {"Geral": ["Geral"]}
            
            # Filtra chaves de configuração invisíveis do layout
            setores_existentes = [k for k in empresa['org_structure'].keys() if not k.startswith('_')]
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.subheader("1. Criar ou Remover Setores")
                new_setor = st.text_input("Nome do Novo Setor")
                if st.button("➕ Adicionar Setor", type="primary"):
                    if new_setor and new_setor not in empresa['org_structure']:
                        empresa['org_structure'][new_setor] = []
                        if DB_CONNECTED:
                            try: 
                                supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                            except: pass
                        st.success(f"O setor '{new_setor}' foi criado!")
                        time.sleep(1); st.rerun()
                
                st.markdown("---")
                setor_remover = st.selectbox("Selecione o setor para remover", setores_existentes)
                if st.button("🗑️ Remover Setor"):
                    del empresa['org_structure'][setor_remover]
                    if DB_CONNECTED:
                         try: 
                             supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                         except: pass
                    st.success("Setor removido com sucesso.")
                    time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.subheader("2. Cargos Atrelados ao Setor")
                setor_sel = st.selectbox("Selecione o setor para configurar os cargos:", setores_existentes, key="sel_setor_cargos")
                if setor_sel:
                    df_cargos = pd.DataFrame({"Cargo": empresa['org_structure'][setor_sel]})
                    edited_cargos = st.data_editor(df_cargos, num_rows="dynamic", key="editor_cargos", use_container_width=True)
                    if st.button("💾 Salvar Lista de Cargos", type="primary"):
                        lista_nova = edited_cargos["Cargo"].dropna().tolist()
                        empresa['org_structure'][setor_sel] = lista_nova
                        if DB_CONNECTED:
                             try: 
                                 supabase.table('companies').update({"org_structure": empresa['org_structure']}).eq('id', empresa['id']).execute()
                             except: pass
                        st.success("A lista de cargos foi atualizada e guardada.")
                st.markdown("</div>", unsafe_allow_html=True)

    elif selected == "Links de Pesquisa":
        st.title("Links de Pesquisa e Convites")
        if not visible_companies: 
            st.warning("⚠️ Precisa primeiro cadastrar um cliente antes de gerar o link."); return
            
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            empresa_nome = st.selectbox("Selecione a empresa:", [c['razao'] for c in visible_companies])
            empresa = next(c for c in visible_companies if c['razao'] == empresa_nome)
            
            base_url = st.session_state.platform_config.get('base_url', 'https://elonr01-cris.streamlit.app').rstrip('/')
            link_final = f"{base_url}/?cod={empresa['id']}"
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("##### Link de Acesso para os Colaboradores")
                st.markdown(f"<div style='background-color: #f8f9fa; border: 1px dashed #dee2e6; padding: 15px; border-radius: 8px; font-family: monospace; color: #2c3e50; font-weight: bold; word-break: break-all; margin-bottom: 5px;'>{link_final}</div>", unsafe_allow_html=True)
                
                # BOTÃO DE CÓPIA DO LINK VIA COMPONENTE HTML
                st.components.v1.html(get_copy_button_html(link_final, "📋 Copiar Link Oficial"), height=55)
                
                limit = empresa.get('limit_evals', 999999)
                usadas = empresa.get('respondidas', 0)
                val = empresa.get('valid_until', '-')
                try: val = datetime.date.fromisoformat(val).strftime('%d/%m/%Y')
                except: pass
                st.caption(f"📊 Avaliações Utilizadas: {usadas} de {limit} disponíveis.")
                st.caption(f"📅 O Link será válido até: {val}")
                st.caption(f"🧠 Metodologia escolhida para a pesquisa: **{empresa.get('metodologia', 'HSE-IT (35 itens)')}**")
                
                if st.button("👁️ Visualizar Pesquisa (Como o colaborador verá)"):
                    st.session_state.current_company = empresa
                    st.session_state.logged_in = True
                    st.session_state.user_role = 'colaborador'
                    st.rerun()
            with c2:
                st.markdown("##### QR Code de Acesso")
                qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(link_final)}"
                st.image(qr_api_url, width=150)
                st.markdown(f"[📥 Baixar QR Code]({qr_api_url})")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("##### 💬 Mensagem de Convite Pronta (WhatsApp / E-mail)")
            texto_convite = f"""Olá, equipe da {empresa['razao']}! 👋

Cuidar dos nossos resultados é muito importante, mas nada disso faz sentido se não cuidarmos, em primeiro lugar, de quem faz tudo acontecer: vocês.

Para construirmos um ambiente de trabalho cada vez melhor, mais leve e saudável, precisamos muito da ajuda e transparência de vocês. Estamos lançando a nossa Pesquisa de Clima e Bem-Estar no Trabalho. 

🧠 **Por que a participação de vocês é tão importante?**
O dia a dia de vocês importa. Muitas vezes o estresse ou a sobrecarga são invisíveis. Responder a este breve questionário permite que a gente veja exatamente onde podemos melhorar, criar novas iniciativas de apoio e corrigir aquilo que não está funcionando tão bem. É a sua voz guiando o nosso trabalho.

🔒 **Privacidade 100% Garantida**
Compreendemos que falar sobre o ambiente de trabalho requer total confiança. Por isso:
- **Anonimato Total:** Utilizamos um sistema seguro onde nenhuma resposta individual consegue ser ligada à pessoa. 
- **Foco na Equipe:** Os resultados chegam até a gestão apenas em formato de gráficos e médias do grupo todo, nunca individuais. Sintam-se perfeitamente seguros e à vontade para serem 100% sinceros.

🚀 **Como participar?**
A avaliação leva apenas cerca de 7 minutos. Cliquem no link seguro abaixo através do seu celular ou computador:

🔗 Acessar a Pesquisa: {link_final}

Agradecemos imensamente o seu tempo e o seu compartilhamento. Só com a sua honestidade é que conseguiremos fazer do nosso espaço, um lugar cada vez melhor para todos.

Atenciosamente,
Equipe de Recursos Humanos e Liderança"""
            
            # Caixa de edição do texto, capturando sempre a versão atual
            texto_editado = st.text_area("Você pode editar o modelo abaixo antes de copiar e enviar aos colaboradores:", value=texto_convite, height=450)
            
            # BOTÃO DE CÓPIA DO TEXTO VIA COMPONENTE HTML
            st.components.v1.html(get_copy_button_html(texto_editado, "📋 Copiar Mensagem de Convite"), height=55)
            
            st.markdown("</div>", unsafe_allow_html=True)

    elif selected == "Relatórios e Laudos":
        st.title("Geração de Relatórios e Laudos Técnicos")
        if not visible_companies: 
            st.warning("É preciso ter empresas cadastradas e com respostas para emitir um relatório."); return
            
        c_sel, c_blank = st.columns([1, 1])
        with c_sel:
            empresa_sel = st.selectbox("Selecione a empresa para gerar o relatório:", [e['razao'] for e in visible_companies])
        
        empresa = next(e for e in visible_companies if e['razao'] == empresa_sel)
        metodo_ativo = empresa.get('metodologia', 'HSE-IT (35 itens)')
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("#### Assinaturas do Relatório")
            sig_empresa_nome = st.text_input("Nome do Responsável (Cliente)", value=empresa.get('resp',''))
            sig_empresa_cargo = st.text_input("Cargo do Responsável", value="Direção")
            sig_tecnico_nome = st.text_input("Nome do Consultor Técnico (Você)", value="Cristiane Cardoso Lima")
            sig_tecnico_cargo = st.text_input("Cargo do Consultor", value="Consultoria em Saúde Mental e RH - Pessin Gestão")

        dimensoes_atuais = empresa.get('dimensoes', {})
        analise_auto = gerar_analise_robusta(dimensoes_atuais)
        sugestoes_auto = gerar_banco_sugestoes(dimensoes_atuais)
        
        if st.session_state.acoes_list is None: 
            st.session_state.acoes_list = []
            
        if not st.session_state.acoes_list and sugestoes_auto:
            for s in sugestoes_auto: 
                st.session_state.acoes_list.append({
                    "acao": s['acao'], 
                    "estrat": s['estrat'], 
                    "area": s['area'], 
                    "resp": "A Definir em Reunião", 
                    "prazo": "30 a 60 dias"
                })
        
        html_act = ""
        if st.session_state.acoes_list:
            for item in st.session_state.acoes_list:
                html_act += f"<tr><td>{item.get('acao','')}</td><td>{item.get('estrat','')}</td><td>{item.get('area','')}</td><td>{item.get('resp','')}</td><td>{item.get('prazo','')}</td></tr>"
        else:
            html_act = "<tr><td colspan='5' style='text-align:center;'>Nenhuma ação definida no plano.</td></tr>"

        with st.expander("📝 Personalização do Relatório e Plano de Ação", expanded=True):
            st.markdown("##### 1. Parecer Técnico Conclusivo")
            analise_texto = st.text_area("Adapte este texto com a sua avaliação técnica. É ele que irá constar na conclusão principal do Laudo entregue ao cliente:", value=analise_auto, height=150)
            
            st.markdown("---")
            st.markdown("##### 2. Banco de Sugestões para o Plano de Ação")
            opcoes_formatadas = [f"[{s['area']}] {s['acao']}: {s['estrat']}" for s in sugestoes_auto]
            selecionadas = st.multiselect("Selecione ações recomendadas para adicionar ao plano do cliente:", options=opcoes_formatadas)
            if st.button("⬇️ Adicionar Ações Selecionadas ao Plano", type="secondary"):
                novas = []
                for item_str in selecionadas:
                    for s in sugestoes_auto:
                        if f"[{s['area']}] {s['acao']}: {s['estrat']}" == item_str:
                            novas.append({
                                "acao": s['acao'], 
                                "estrat": s['estrat'], 
                                "area": s['area'], 
                                "resp": "Liderança e RH", 
                                "prazo": "Acompanhamento em 90 dias"
                            })
                st.session_state.acoes_list.extend(novas)
                st.success("Táticas de gestão adicionadas com sucesso à lista!")
                st.rerun()
                
            st.markdown("##### 3. Plano de Ação Estratégico (Editável)")
            st.info("Edite os campos abaixo com dois cliques rápidos. Você pode alterar prazos, responsáveis, e adicionar novas linhas na última aba em branco para moldar o plano perfeitamente ao cliente. O que escrever aqui irá diretamente para o PDF.")
            
            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.acoes_list), 
                num_rows="dynamic", 
                use_container_width=True, 
                column_config={
                    "acao": "Título Específico da Ação Macro", 
                    "estrat": st.column_config.TextColumn("Estratégia e Execução Desdobrada", width="large"), 
                    "area": "Domínio ou Área Alvo", 
                    "resp": "Ator Responsável (Líder)", 
                    "prazo": "Marca Temporal Limite (SLA)"
                }
            )
            
            if not edited_df.empty: 
                st.session_state.acoes_list = edited_df.to_dict('records')

        if st.button("📥 Gerar e Baixar Laudo Técnico (HTML/PDF)", type="primary"):
            st.markdown("---")
            logo_html = get_logo_html(150)
            logo_cliente_html = ""
            if empresa.get('logo_b64'):
                logo_cliente_html = f"<img src='data:image/png;base64,{empresa.get('logo_b64')}' width='110' style='float:right; margin-left: 15px; border-radius:4px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);'>"
            
            html_dimensoes = ""
            if empresa.get('dimensoes'):
                for dim, nota in empresa.get('dimensoes', {}).items():
                    cor_card = COR_RISCO_ALTO if nota < 3 else (COR_RISCO_MEDIO if nota < 4 else COR_RISCO_BAIXO)
                    label_card = "CENÁRIO CRÍTICO" if nota < 3 else ("MOMENTO DE ATENÇÃO" if nota < 4 else "AMBIENTE SEGURO")
                    html_dimensoes += f"""
                    <div style="flex: 1; min-width: 85px; background-color: #fcfcfc; border: 1px solid #e0e0e0; padding: 8px; border-radius: 6px; margin: 4px; text-align: center; font-family: 'Helvetica Neue', Helvetica, sans-serif; box-shadow: inset 0 -2px 0 {cor_card};">
                        <div style="font-size: 8px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold;">{dim}</div>
                        <div style="font-size: 16px; font-weight: 800; color: {cor_card}; margin: 4px 0;">{nota:.1f}</div>
                        <div style="font-size: 7px; color: #777; background: #eee; padding: 2px; border-radius: 2px;">{label_card}</div>
                    </div>
                    """

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
                     val = detalhes_heatmap.get(q['q']) 
                     
                     if val is None:
                         c_bar = "#cccccc" 
                         txt_exposicao = "Dados Insuficientes"
                         val_width = 0
                     else:
                         c_bar = COR_RISCO_ALTO if val >= 55 else (COR_RISCO_MEDIO if val > 20 else COR_RISCO_BAIXO)
                         txt_exposicao = f"{val}% Nível de Exposição ao Fator"
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
                html_act_final = "<tr><td colspan='5' style='text-align: center; padding: 20px; color: #999;'>Não há um plano de ação formulado para esta avaliação.</td></tr>"

            score_final_empresa = empresa.get('score', 0)
            score_width_css = (score_final_empresa / 5.0) * 100
            
            html_gauge_css = f"""
            <div style="text-align: center; padding: 15px; font-family: 'Helvetica Neue', Helvetica, sans-serif;">
                <div style="font-size: 32px; font-weight: 900; color: {COR_PRIMARIA}; text-shadow: 1px 1px 0px rgba(0,0,0,0.05);">
                    {score_final_empresa:.2f} <span style="font-size: 14px; font-weight: normal; color: #a0a0a0;">/ de 5.00 possiveis</span>
                </div>
                <div style="width: 100%; background: #e0e0e0; height: 16px; border-radius: 8px; margin-top: 10px; position: relative; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="position: absolute; left: 0; top: 0; width: {score_width_css}%; background: linear-gradient(90deg, {COR_PRIMARIA} 0%, {COR_SECUNDARIA} 100%); height: 16px; border-radius: 8px;"></div>
                </div>
                <div style="font-size: 10px; color: #7f8c8d; margin-top: 8px; letter-spacing: 1px; text-transform: uppercase;">
                    Grau Global de Saúde e Bem-Estar da Equipe
                </div>
            </div>
            """
            
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
                        <th style="text-align: left; padding: 8px 10px; border-bottom: 2px solid #ddd; color: #555;">Dimensão Psicológica Investigada</th>
                        <th style="text-align: right; padding: 8px 10px; border-bottom: 2px solid #ddd; color: #555;">Nota Final Obtida (Média)</th>
                    </tr>
                </thead>
                <tbody>
                    {html_radar_rows}
                </tbody>
            </table>
            """

            lgpd_note = f"""
            <div style="margin-top: 40px; border-top: 1px solid #ccc; padding-top: 15px; font-size: 8px; color: #888; text-align: justify; font-family: 'Helvetica Neue', Helvetica, sans-serif; line-height: 1.4;">
                <strong>TERMO ASSINADO DE ESTREITA CONFIDENCIALIDADE E PROTEÇÃO IRREVOGÁVEL E ESTRITA DE BANCO DADOS (SISTEMAS LGPD):</strong> Este instrumento avaliativo em escala profissional e científica de saúde ocupacional focado na raiz corporativa baseou-se tecnicamente em laços criados e foi confeccionado estritamente utilizando os mais complexos e densos métodos atuais de criptografia de banco de dados e rotinas imutáveis de obfuscação algorítmica de identidades. Os resultados e gráficos apresentados garantem o total anonimato de quem participou, exibindo apenas dados e médias coletivas sem qualquer correlação de nome e respostas. (Em conformidade total com a Lei Geral de Proteção de Dados - Lei nº 13.709/2018).
            </div>
            """

            raw_html = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="utf-8">
                <title>Dossiê Técnico Institucional - Matriz Oficial {empresa['razao']}</title>
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
                        <div style="font-size: 22px; font-weight: 900; color: {COR_PRIMARIA}; letter-spacing: -0.5px;">LAUDO DE SAÚDE MENTAL E CLIMA ({metodo_ativo})</div>
                        <div style="font-size: 12px; color: #7f8c8d; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px;">Relatório Oficial de Gestão de Fatores e Riscos Psicossociais no Ambiente de Trabalho</div>
                    </div>
                </header>

                <div class="caixa-destaque">
                    {logo_cliente_html}
                    <div style="font-size: 10px; color: #95a5a6; margin-bottom: 6px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">DADOS DA EMPRESA</div>
                    <div style="font-weight: 900; font-size: 18px; margin-bottom: 8px; color: #2c3e50;">{empresa.get('razao', '-')}</div>
                    
                    <div style="display: flex; gap: 40px; margin-top: 15px;">
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Identificação Oficial (CNPJ)</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">{empresa.get('cnpj','-')}</div>
                        </div>
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Total de Participantes (Adesão)</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">O diagnóstico contou com a participação efetiva de {empresa.get('respondidas',0)} colaboradores(as).</div>
                        </div>
                        <div>
                            <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Data de Emissão do Laudo</div>
                            <div style="font-size: 11px; font-weight: 600; color: #34495e;">{datetime.datetime.now().strftime('%d/%m/%Y')}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; border-top: 1px dashed #ddd; padding-top: 10px;">
                        <div style="font-size: 9px; color: #7f8c8d; text-transform: uppercase;">Endereço e Instalações Auditadas</div>
                        <div style="font-size: 11px; color: #34495e;">{empresa.get('endereco','-')}</div>
                    </div>
                </div>

                <h4>1. OBJETIVO DA AVALIAÇÃO</h4>
                <p style="text-align: justify; font-size: 11px; color: #555;">
                    O presente relatório executivo baseia-se nas normas e práticas validadas da metodologia <strong>{metodo_ativo}</strong>. O principal objetivo desta avaliação é identificar, com rigor, a extensão dos fatores de bem-estar ou o nível de desgaste presente no ambiente de trabalho das equipes da organização avaliada.<br><br>Através da participação anônima da equipe e de ferramentas matemáticas robustas na nuvem, conseguimos mapear a realidade da organização de uma forma que atende plenamente às diretrizes e boas práticas exigidas pelo Ministério relativas à prevenção e Gestão de Riscos Ocupacionais (GRO/PGR).
                </p>

                <div class="colunas-flex">
                    <div class="coluna-dado">
                        <div class="titulo-coluna">2. SCORE GERAL (VISÃO GLOBAL)</div>
                        {html_gauge_css}
                    </div>
                    <div class="coluna-dado">
                        <div class="titulo-coluna">3. RESULTADO MÉDIO CONSOLIDADO POR DIMENSÃO</div>
                        {html_radar_table}
                    </div>
                </div>

                <h4>4. MAPA DE DIAGNÓSTICO DETALHADO POR CADA DIMENSÃO DE SAÚDE</h4>
                <div style="display: flex; flex-wrap: wrap; margin-bottom: 30px; gap: 8px;">
                    {html_dimensoes}
                </div>

                <h4>5. VARREDURA RAIO-X REPASSANDO EXAUSTIVAMENTE OS FATORES AVALIADOS COM A EQUIPE</h4>
                <p style="font-size: 10px; color: #777; margin-bottom: 15px; margin-top: -10px; font-style: italic;">
                    Nota técnica para interpretação: As representações visuais abaixo mostram de forma simples o nível percentual de risco contínuo detectado para cada situação. Barras com porcentagens altas (cores mais quentes como laranja e vermelho) representam áreas que devem ser abordadas prioritariamente pela Gestão e pelos Recursos Humanos.
                </p>
                <div class="grid-raiox">
                    {html_x}
                </div>

                <div style="page-break-before: always;"></div>

                <h4>6. PLANO DE AÇÃO ESTRATÉGICO SUGERIDO (COMPLIANCE E PREVENÇÃO)</h4>
                <p style="font-size: 10px; color: #777; margin-bottom: 15px; margin-top: -10px; font-style: italic;">
                    As sugestões descritas na tabela de apoio que se segue foram refinadas sob intervenção humana e com base nos scores coletados. As estratégias procuram atacar as maiores fragilidades encontradas no radar e no mapeamento comportamental com sugestões práticas aplicáveis.
                </p>
                <table style="width: 100%; border-collapse: collapse; font-size: 10px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; box-shadow: 0 0 0 1px #eef2f5; border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background-color: {COR_PRIMARIA}; color: #ffffff;">
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">TÍTULO DO PLANO / AÇÃO MACRO</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">ESTRATÉGIA PRÁTICA E EXECUÇÃO</th>
                            <th style="padding: 12px 10px; text-align: center; font-weight: 600; letter-spacing: 0.5px;">FOCO DE ÁREA</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">RESPONSÁVEL (LIDERANÇA)</th>
                            <th style="padding: 12px 10px; text-align: left; font-weight: 600; letter-spacing: 0.5px;">MARCA TEMPORAL (SLA/PRAZO)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_act_final}
                    </tbody>
                </table>

                <h4>7. PARECER TÉCNICO FORMAL DA CONSULTORIA DE RH</h4>
                <div style="text-align: justify; font-size: 11px; line-height: 1.8; background-color: #f8fbfc; padding: 25px; border-radius: 8px; border: 1px solid #eef2f5; color: #444; white-space: pre-wrap;">
                    {analise_texto}
                </div>

                <div style="margin-top: 80px; display: flex; justify-content: space-around; gap: 60px;">
                    <div style="flex: 1; text-align: center; border-top: 1px solid #2c3e50; padding-top: 12px;">
                        <div style="font-weight: 800; font-size: 12px; color: #2c3e50; text-transform: uppercase;">{sig_empresa_nome}</div>
                        <div style="color: #7f8c8d; font-size: 10px; margin-top: 4px;">{sig_empresa_cargo}</div>
                        <div style="color: #95a5a6; font-size: 9px; margin-top: 2px;">Assinatura por delegação (Representante Legal)</div>
                    </div>
                    <div style="flex: 1; text-align: center; border-top: 1px solid #2c3e50; padding-top: 12px;">
                        <div style="font-weight: 800; font-size: 12px; color: #2c3e50; text-transform: uppercase;">{sig_tecnico_nome}</div>
                        <div style="color: #7f8c8d; font-size: 10px; margin-top: 4px;">{sig_tecnico_cargo}</div>
                        <div style="color: #95a5a6; font-size: 9px; margin-top: 2px;">Chancela Técnica Eletrônica do Avaliador(a) Pericial</div>
                    </div>
                </div>
                
                {lgpd_note}
            </body>
            </html>
            """
            
            b64_pdf = base64.b64encode(raw_html.encode('utf-8')).decode('utf-8')
            
            st.markdown(f"""
            <a href="data:text/html;base64,{b64_pdf}" download="Laudo_Tecnico_Gestao_RH_{empresa["id"]}.html" style="
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
                ⬇️ BAIXAR LAUDO TÉCNICO CORPORATIVO (ARQUIVO HTML PARA CONVERSÃO EM PDF)
            </a>
            """, unsafe_allow_html=True)
            
            st.info("💡 **Dica de Consultoria (Como extrair um PDF perfeito):** Após o arquivo ser baixado, clique para abri-lo no seu navegador. Em seguida, pressione `Ctrl + P` (ou `Cmd + P` no Mac) e escolha a opção para **Salvar como PDF**. Desative a impressão de Cabeçalhos e Rodapés e ative sempre os **'Gráficos de Plano de Fundo'** para que todas as cores da nossa marca fiquem intactas no papel.")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Visualização da Estrutura Final do Relatório (Preview):")
            st.components.v1.html(raw_html, height=1000, scrolling=True)

    elif selected == "Histórico de Evolução":
        st.title("Histórico e Comparativo de Evolução")
        if not visible_companies: 
            st.warning("É preciso ter um histórico de empresas a ser analisado para utilizar esta função."); return
        
        empresa_nome = st.selectbox("Selecione a empresa:", [c['razao'] for c in visible_companies])
        empresa = next((c for c in visible_companies if c['razao'] == empresa_nome), None)
        
        if empresa:
            metodo_nome_ativo = empresa.get('metodologia', 'HSE-IT (35 itens)')
            questoes_ativas = st.session_state.methodologies.get(metodo_nome_ativo, st.session_state.methodologies['HSE-IT (35 itens)'])['questions']
            
            history_data = generate_real_history(empresa['id'], responses_data, questoes_ativas, empresa.get('func', 1))
            
            if not history_data:
                st.info("ℹ️ Ops! Ainda não temos avaliações antigas para fazer a comparação. As métricas vão aparecer aqui no próximo ciclo de avaliação desta equipe.")
            else:
                tab_evo, tab_comp = st.tabs(["📈 Evolução do Score Geral", "⚖️ Comparativo de Dimensões (Radar A x B)"])
                
                with tab_evo:
                    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                    df_hist = pd.DataFrame(history_data)
                    fig_line = px.line(
                        df_hist, 
                        x='periodo', 
                        y='score', 
                        markers=True, 
                        title=f"Evolução do Fator de Segurança Geral - {metodo_nome_ativo}"
                    )
                    fig_line.update_traces(
                        line_color=COR_SECUNDARIA, 
                        line_width=4, 
                        marker=dict(size=12, color=COR_PRIMARIA, line=dict(width=2, color='white'))
                    )
                    fig_line.update_layout(
                        yaxis_range=[1, 5],
                        plot_bgcolor='#fafbfc',
                        xaxis_title="Janela de Avaliação",
                        yaxis_title="Score do Algoritmo (1 a 5)"
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with tab_comp:
                    if len(history_data) < 2:
                        st.warning("⚠️ Ainda não temos dados suficientes para ancorar um comparativo. Precisamos de avaliações em pelo menos dois períodos diferentes.")
                    else:
                        st.write("Defina as datas que deseja comparar para entender se o plano de ação resultou.")
                        c1, c2 = st.columns(2)
                        periodo_a = c1.selectbox("Período A (Referência Anterior)", [h['periodo'] for h in history_data], index=1)
                        periodo_b = c2.selectbox("Período B (Avaliação Atual)", [h['periodo'] for h in history_data], index=0)
                        
                        dados_a = next((h for h in history_data if h['periodo'] == periodo_a), None)
                        dados_b = next((h for h in history_data if h['periodo'] == periodo_b), None)
                        
                        if dados_a and dados_b:
                            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                            categories = list(dados_a['dimensoes'].keys())
                            fig_comp = go.Figure()
                            
                            fig_comp.add_trace(go.Scatterpolar(
                                r=list(dados_a['dimensoes'].values()), 
                                theta=categories, 
                                fill='toself', 
                                name=f'Referência de: {periodo_a}', 
                                line_color=COR_COMP_A, 
                                opacity=0.4
                            ))
                            
                            fig_comp.add_trace(go.Scatterpolar(
                                r=list(dados_b['dimensoes'].values()), 
                                theta=categories, 
                                fill='toself', 
                                name=f'Resultado de: {periodo_b}', 
                                line_color=COR_COMP_B, 
                                opacity=0.8
                            ))
                            
                            fig_comp.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                                title=f"Sobreposição do Radar Comparativo ({metodo_nome_ativo})"
                            )
                            st.plotly_chart(fig_comp, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            if st.button("📥 Sintetizar e Baixar Documento Comparativo Oficial", type="primary"):
                                 logo_html = get_logo_html(150)
                                 
                                 diff_score = dados_b['score'] - dados_a['score']
                                 txt_evolucao = "uma melhoria clara na estabilidade mental das equipes." if diff_score > 0 else "um momento que exige muita vigilância e atuação imediata devido à queda geral nas notas das equipes."
                                 
                                 chart_css_viz = f"""
                                 <div style="padding: 25px; border: 1px solid #e0e6ed; border-radius: 12px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.03);">
                                     <div style="margin-bottom: 25px;">
                                         <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                             <strong style="color: #34495e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Nota Geral de Saúde Ocupacional no Período de [{periodo_a}]:</strong> 
                                             <span style="font-size: 24px; font-weight: 900; color: {COR_COMP_A}">{dados_a['score']} <span style="font-size: 12px; color: #aab7b8;">/ de 5.0</span></span>
                                         </div>
                                         <div style="width: 100%; background: #ecf0f1; height: 18px; border-radius: 9px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);">
                                            <div style="width: {(dados_a['score']/5)*100}%; background: {COR_COMP_A}; height: 18px; border-radius: 9px;"></div>
                                         </div>
                                     </div>
                                     <div>
                                         <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                                             <strong style="color: #34495e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Nota Geral de Saúde Ocupacional no Período de [{periodo_b}]:</strong> 
                                             <span style="font-size: 24px; font-weight: 900; color: {COR_COMP_B}">{dados_b['score']} <span style="font-size: 12px; color: #aab7b8;">/ de 5.0</span></span>
                                         </div>
                                         <div style="width: 100%; background: #ecf0f1; height: 18px; border-radius: 9px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);">
                                            <div style="width: {(dados_b['score']/5)*100}%; background: {COR_COMP_B}; height: 18px; border-radius: 9px;"></div>
                                         </div>
                                     </div>
                                 </div>
                                 """

                                 html_comp = f"""
                                 <!DOCTYPE html>
                                 <html lang="pt-BR">
                                 <head>
                                     <meta charset="utf-8">
                                     <title>Relatório Evolutivo em Dados</title>
                                     <style>
                                         body {{ font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px 30px; color: #2c3e50; background: white; line-height: 1.6; }}
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
                                             <div style="font-size:11px;"><strong>Janelas Comparativas:</strong> <span style="color:{COR_PRIMARIA}; font-weight: bold; background: #eef2f5; padding: 2px 6px; border-radius: 4px;">{periodo_a}</span> VERSUS <span style="color:{COR_PRIMARIA}; font-weight: bold; background: #eef2f5; padding: 2px 6px; border-radius: 4px;">{periodo_b}</span></div>
                                         </div>
                                     </div>
                                     
                                     <h4>1. PAINEL DE INDICADORES DE DESEMPENHO</h4>
                                     <table class="tabela-kpi">
                                         <tr>
                                             <th>SINTOMA / INDICADOR ANALISADO</th>
                                             <th>MARCO REFERÊNCIA [{periodo_a}]</th>
                                             <th>MARCO ATUAL [{periodo_b}]</th>
                                             <th>VARIAÇÃO LÍQUIDA (DELTA)</th>
                                         </tr>
                                         <tr>
                                             <td>Score Geral da Organização (Cálculo Composto)</td>
                                             <td>{dados_a['score']}</td>
                                             <td>{dados_b['score']}</td>
                                             <td style="font-weight:900; color:{'#27ae60' if diff_score > 0 else '#c0392b'};">{diff_score:+.2f} pts</td>
                                         </tr>
                                         <tr>
                                             <td>Taxa Bruta de Adesão Censitária das Equipes (%)</td>
                                             <td>{dados_a['adesao']}%</td>
                                             <td>{dados_b['adesao']}%</td>
                                             <td style="font-weight:bold; color:#7f8c8d;">{(dados_b['adesao'] - dados_a['adesao']):+.1f}%</td>
                                         </tr>
                                     </table>
                                     
                                     <h4>2. EQUILÍBRIO GRÁFICO</h4>
                                     {chart_css_viz}
                                     
                                     <h4>3. CONCLUSÃO E ANÁLISE TÉCNICA DOS RESULTADOS</h4>
                                     <p style="text-align:justify; font-size:12px; line-height:1.7; background:#fbfcfd; padding:20px; border-radius:8px; border: 1px solid #eef2f5; color: #444;">A análise estruturada, resultante da comparação exata entre as duas janelas de tempo apresentadas, demonstrou <strong>{txt_evolucao}</strong> Recomendamos fortemente a direção da empresa, juntamente com o seu RH, a avaliarem com minúcia as dimensões de perigo mais salientes e a porem em prática de imediato novos planos de ações preventivas para melhoria da cultura geral de satisfação e bem-estar nas dependências da companhia.</p>
                                     
                                     <div class="rodape">
                                         Plataforma Elo NR-01 Enterprise Core | Inteligência e Gestão Humanizada em Dados de Saúde Ocupacional<br>Documento Oficial e Privado
                                     </div>
                                 </body>
                                 </html>
                                 """
                                 
                                 b64_comp = base64.b64encode(html_comp.encode('utf-8')).decode('utf-8')
                                 
                                 st.markdown(f"""
                                 <a href="data:text/html;base64,{b64_comp}" download="Dossie_Evolutivo_RH_{empresa["id"]}.html" style="
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
                                     📥 DOWNLOAD DO RELATÓRIO COMPARATIVO (HTML)
                                 </a>
                                 """, unsafe_allow_html=True)
                                 st.caption("Apoie os seus líderes com este dossiê. Lembre-se, pressione `Ctrl+P` no navegador para gerar em PDF e envie a eles.")

    elif selected == "Configurações":
        if perm == "Master":
            st.title("Configurações da Plataforma")
            t1, t2, t3 = st.tabs(["👥 Gerenciamento de Usuários", "🎨 Identidade Visual e Marca", "⚙️ Configurações de Servidor (URL)"])
            
            with t1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Acessos à Plataforma")
                
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
                new_u = c1.text_input("Novo Usuário (Login)")
                new_p = c2.text_input("Senha", type="password")
                new_r = st.selectbox("Nível de Acesso", ["Master", "Gestor", "Analista"])
                
                if st.button("➕ Confirmar Criação do Usuário", type="primary"):
                    if not new_u or not new_p: 
                        st.error("Usuário e Senha são campos obrigatórios.")
                    else:
                        if DB_CONNECTED:
                            try:
                                supabase.table('admin_users').insert({"username": new_u, "password": new_p, "role": new_r, "credits": 999999 if new_r=="Master" else 500}).execute()
                                st.success(f"✅ Boa! O usuário [{new_u}] foi criado e já pode entrar no sistema!")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e: 
                                st.error(f"Engasgo na gravação remota: {e}")
                        else:
                            st.session_state.users_db[new_u] = {"password": new_p, "role": new_r, "credits": 999999}
                            st.success(f"✅ Usuário [{new_u}] guardado apenas no seu modo local!")
                            time.sleep(1)
                            st.rerun()
                
                st.markdown("---")
                st.write("### Remover Usuário")
                users_op = [u['username'] for u in usrs_raw if u['username'] != curr_user]
                if users_op:
                    u_del = st.selectbox("Selecione cuidadosamente o usuário para remover:", users_op)
                    if st.button("🗑️ REMOVER USUÁRIO SELECIONADO DA BASE", type="primary"): 
                        delete_user(u_del)
                else:
                    st.info("De momento não há outros usuários elegíveis para remoção.")
                st.markdown("</div>", unsafe_allow_html=True)

            with t2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Identidade Visual e Marca")
                nn = st.text_input("Nome da Plataforma (Mostrado no topo e relatórios)", value=st.session_state.platform_config.get('name', 'Elo NR-01'))
                nc = st.text_input("Nome da Consultoria em RH (A sua empresa)", value=st.session_state.platform_config.get('consultancy', ''))
                nl = st.file_uploader("Upload de Logotipo (PNG ou JPG com fundo transparente)", type=['png', 'jpg', 'jpeg'])
                
                if st.button("💾 Guardar Marca Personalizada", type="primary"):
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
                            st.success("✅ A sua marca foi guardada perfeitamente na base de dados!")
                        except Exception as e: 
                            st.warning(f"Erro na tentativa de guardar (Salvo localmente): {e}")
                    else:
                        st.success("✅ Logotipo e nome modificados.")
                        
                    st.session_state.platform_config = new_conf
                    time.sleep(1.5)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with t3:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.write("### Configurações de Servidor (URL)")
                base = st.text_input("Endereço Web Atual (Crucial para os links enviados aos colaboradores funcionarem)", value=st.session_state.platform_config.get('base_url', ''))
                
                if st.button("🔗 Gravar e Atualizar URL do Sistema", type="primary"):
                    new_conf = st.session_state.platform_config.copy()
                    new_conf['base_url'] = base
                    
                    if DB_CONNECTED:
                        try:
                            res = supabase.table('platform_settings').select("*").execute()
                            if res.data: 
                                supabase.table('platform_settings').update({"config_json": new_conf}).eq("id", res.data[0]['id']).execute()
                            else: 
                                supabase.table('platform_settings').insert({"config_json": new_conf}).execute()
                            st.success("✅ O seu URL foi atualizado e guardado de forma permanente.")
                        except Exception as e: 
                            st.warning(f"Erro na nuvem: {e}")
                    else:
                        st.success("✅ Atualização gravada com sucesso.")

                    st.session_state.platform_config = new_conf
                    time.sleep(1.5)
                    st.rerun()
                    
                st.markdown("---")
                st.write("### O Coração da Plataforma (Base de Dados)")
                if DB_CONNECTED: 
                    st.info("🟢 O sistema encontra-se com ligação verde (estável e forte) ao Supabase em Nuvem. Todas as suas salvaguardas vão ficar disponíveis perenemente para si ou clientes na web sem quaisquer problemas.")
                else: 
                    st.error("🔴 Nota Limiar: A sua interligação ao Cofre Cloud não logrou autenticar por motivos de rede. De momento está no regime 'offline' da sua máquina. O aplicativo foi reposto e corre pela memória provisória do browser. Qualquer refresh que seja feito ou F5 poderá levar à perda definitiva do processo que está na memória.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("🚫 Apenas Administradores do nível 'Master' (Sênior) têm permissão para acessar esta página do programa.")

# ==============================================================================
# 6. MÓDULO DOS COLABORADORES (A PESQUISA DE CLIMA E SAÚDE)
# ==============================================================================
def survey_screen():
    """A interface limpa e acolhedora onde as equipes respondem à avaliação de forma sigilosa e leve."""
    cod = st.query_params.get("cod")
    
    comp = None
    
    # 1. VERIFICAÇÃO MODO PREVIEW (RH VISUALIZANDO)
    if not cod and st.session_state.get('user_role') == 'colaborador' and st.session_state.get('current_company'):
        comp = st.session_state.current_company
    else:
        # 2. ACESSO REAL (VIA LINK DO COLABORADOR)
        if DB_CONNECTED and cod:
            try:
                res = supabase.table('companies').select("*").eq('id', cod).execute()
                if res.data: comp = res.data[0]
            except: pass
            
        if not comp and cod: 
            comp = next((c for c in st.session_state.companies_db if str(c['id']) == str(cod)), None)
    
    # 3. TRATATIVA DE ERRO DE LINK INVÁLIDO
    if not comp: 
        st.error("❌ Código de Rastreio Inválido. Pedimos que tente acessar novamente e confirme junto ao líder de Recursos Humanos se o seu link foi bem encaminhado e enviado sem erro de digitação.")
        # Fallback para o RH voltar caso se perca
        if st.session_state.get('admin_permission'):
            if st.button("⬅️ Voltar ao Painel Administrativo"):
                st.session_state.user_role = 'admin'
                st.rerun()
        return
        
    # 4. BOTÃO DE VOLTAR EXCLUSIVO PARA O MODO PREVIEW DO RH
    is_preview = st.session_state.get('admin_permission') is not None and st.session_state.get('user_role') == 'colaborador'
    if is_preview:
        st.info("👁️ **Modo Visualização Ativo:** Você está vendo esta tela exatamente como o colaborador a verá. Enviar respostas aqui afetará os gráficos da empresa.")
        if st.button("⬅️ Sair da Visualização e Voltar ao Painel", type="secondary"):
            st.session_state.user_role = 'admin'
            st.session_state.current_company = None
            st.rerun()
        st.markdown("---")

    # 5. VALIDAÇÃO DE DATA E COTA (Pula os bloqueios se for o RH visualizando)
    if comp.get('valid_until') and not is_preview:
        try:
            if datetime.date.today() > datetime.date.fromisoformat(comp['valid_until']):
                st.error("⛔ O link fornecido para a sua empresa já se encontra inativo ou expirado.")
                return
        except: pass
        
    limit_evals = comp.get('limit_evals', 999999)
    resp_count = comp.get('respondidas', 0) if comp.get('respondidas') is not None else 0
    if resp_count >= limit_evals and not is_preview:
        st.error("⚠️ Pedimos desculpas. Infelizmente já foi atingido o número limite de respostas para este projeto em particular. Obrigado pela boa vontade em compartilhar e apoiar.")
        return
    
    # Resgata a metodologia amarrada a empresa
    metodo_nome = comp.get('metodologia', 'HSE-IT (35 itens)')
    metodo_dados = st.session_state.methodologies.get(metodo_nome, st.session_state.methodologies['HSE-IT (35 itens)'])
    perguntas = metodo_dados['questions']

    # Descobre se a empresa exige CPF (Lendo de dentro do JSONB org_structure)
    org_struct = comp.get('org_structure', {})
    exige_cpf = org_struct.get('_exigir_cpf', True) if isinstance(org_struct, dict) else True

    logo = get_logo_html(150)
    if comp.get('logo_b64'): logo = f"<img src='data:image/png;base64,{comp.get('logo_b64')}' width='180'>"
    
    st.markdown(f"<div style='text-align:center; margin-bottom: 20px;'>{logo}</div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color: {COR_PRIMARIA}; font-weight:800; font-family:sans-serif; text-transform:uppercase;'>Pesquisa de Clima e Riscos Psicossociais - {comp['razao']}</h3>", unsafe_allow_html=True)
    
    # Ajuste dinâmico do texto do alerta baseado na exigência de CPF
    if exige_cpf:
        texto_alerta_cpf = "<li>Pedimos a sua identificação de CPF apenas como chave de segurança anti-duplicação, mas fique totalmente tranquilo(a): assim que você clica em enviar, o sistema transforma seu número em um código criptografado, garantindo 100% de anonimato. A empresa nunca saberá quem respondeu o quê.</li>"
    else:
        texto_alerta_cpf = "<li>Sua empresa optou por uma pesquisa <strong>100% livre de identificação prévia</strong>. O preenchimento do CPF foi desativado para garantir a você máximo conforto e anonimato absoluto desde o início.</li>"

    st.markdown(f"""
        <div class='security-alert'>
            <strong>🔒 A SUA PRIVACIDADE É A NOSSA PRIORIDADE</strong><br>
            Sua chefia direta, colegas ou liderança <strong>não terão acesso</strong> a ler o que você escreve individualmente e assinala agora nesta tela.<br>
            <ul>
                {texto_alerta_cpf}
                <li>As estatísticas e gráficos gerados depois serão apenas do grupo como um todo, criando bases práticas para o RH intervir e solucionar questões que afetam toda a equipe.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("survey_form"):
        st.write("#### 1. Seus Dados de Perfil")
        c1, c2 = st.columns(2)
        
        # Renderiza (ou oculta a necessidade) do CPF de forma dinâmica
        if exige_cpf:
            cpf_raw = c1.text_input("CPF (Apenas números, para validação de segurança)")
        else:
            cpf_raw = "N/A"
            c1.info("🟢 A identificação por CPF foi desativada pela sua empresa para esta pesquisa. Siga direto para a escolha do setor.")
        
        s_keys = ["Geral"] 
        if 'org_structure' in comp and isinstance(comp['org_structure'], dict) and comp['org_structure']:
            s_keys = [k for k in comp['org_structure'].keys() if not k.startswith('_')]
             
        setor_colab = c2.selectbox("Selecione o seu setor de atuação atual", s_keys)
        
        st.markdown("---")
        st.write(f"#### 2. Avaliação do Ambiente de Trabalho")
        st.caption("Pense no seu dia a dia ao longo das últimas 4 a 6 semanas e responda de forma muito sincera ao que lhe é perguntado abaixo. Como é que as coisas realmente acontecem para você?")
        
        missing = False
        answers_dict = {}
        
        abas_categorias = list(perguntas.keys())
        tabs = st.tabs(abas_categorias)
        
        for i, (category, questions) in enumerate(perguntas.items()):
            with tabs[i]:
                st.markdown(f"<h5 style='color: {COR_SECUNDARIA}; font-weight:800; text-transform:uppercase; margin-top:20px; margin-bottom: 25px;'>➡️ Categoria: {category}</h5>", unsafe_allow_html=True)
                for q in questions:
                    st.markdown(f"<div style='font-size: 15px; color: #2c3e50; font-weight: 600; margin-bottom: 5px;'>{q['q']}</div>", unsafe_allow_html=True)
                    if q.get('help'):
                        st.caption(f"💡 *{q['help']}*")
                    
                    options = q.get('options', ["Nunca", "Raramente", "Às vezes", "Frequentemente", "Sempre"])
                    
                    response_value = st.radio(
                        "Qual a sua percepção?", 
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
        st.write("#### 3. Termo de Consentimento")
        aceite_lgpd = st.checkbox("Compreendo que a minha participação é voluntária e que as minhas respostas são anônimas e estritamente confidenciais, sendo utilizadas única e exclusivamente para fins de melhoria de qualidade de ambiente de trabalho de acordo e amparado com as normas da base imposta pela Lei Geral de Proteção de Dados (LGPD).")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.form_submit_button("✅ Enviar Minhas Respostas", type="primary", use_container_width=True)
        
        if submit_btn:
            if exige_cpf and (not cpf_raw or len(cpf_raw) < 11 or cpf_raw == "N/A"): 
                st.error("⚠️ Atenção: Por favor verifique e insira o seu documento CPF completo (apenas números) para que o envio seja validado e liberado.")
            elif not aceite_lgpd: 
                st.error("⚠️ Aviso Obrigatório: É necessário marcar a caixa aceitando os termos da garantia e do anonimato seguro (na proteção da lei) para conseguir enviar.")
            elif missing: 
                st.error("⚠️ Atenção: Identificamos que ainda falta preencher algumas opções nas abas acima. Recomendamos revisar cada painel e preencher as lacunas para que o envio da avaliação possa ser registrado.")
            else:
                
                # Se exige CPF, processa o Hash para buscar duplicidade. Senão, cria uma tag aleatória.
                if exige_cpf:
                    hashed_cpf = hashlib.sha256(cpf_raw.encode()).hexdigest()
                    cpf_already_exists = False
                    
                    # Checa duplicidade
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
                else:
                    # Modo livre de CPF: Força sempre passar sem checar duplicidade
                    hashed_cpf = f"anon_livre_{uuid.uuid4().hex}"
                    cpf_already_exists = False

                if cpf_already_exists:
                    st.error("🚫 O protocolo de trava antifraude acabou de interceptar o seu envio. Verificamos que o seu código CPF já foi registrado com sucesso nesta avaliação anteriormente. Visando a integridade estatística, a empresa permite apenas uma avaliação por colaborador.")
                else:
                    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    if DB_CONNECTED:
                        try:
                            supabase.table('responses').insert({
                                "company_id": comp['id'], 
                                "cpf_hash": hashed_cpf,
                                "setor": setor_colab, 
                                "answers": answers_dict, 
                                "created_at": now_str
                            }).execute()
                        except Exception as e: 
                            st.error(f"Engasgo no contato e no procedimento que aloja a base: {e}")
                    else:
                        st.session_state.local_responses_db.append({
                            "company_id": comp['id'], 
                            "cpf_hash": hashed_cpf,
                            "setor": setor_colab, 
                            "answers": answers_dict, 
                            "created_at": now_str
                        })

                    st.success("🎉 Muito obrigado pela sua participação! Suas respostas foram enviadas com sucesso e segurança. Sua opinião é fundamental para construirmos um ambiente de trabalho cada vez melhor.")
                    st.balloons()
                    time.sleep(4.5)
                    
                    # Se for o RH em modo Preview, volta pro admin ao invés de deslogar
                    if is_preview:
                        st.session_state.user_role = 'admin'
                        st.session_state.current_company = None
                    else:
                        st.session_state.logged_in = False 
                        
                    st.rerun()

# ==============================================================================
# 7. ROTAS (ROUTER PRINCIPAL DO SISTEMA)
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
