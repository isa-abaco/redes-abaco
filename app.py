import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from datetime import datetime
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configuração da página
st.set_page_config(
    page_title="Curadoria IA - Colégio Ábaco",
    page_icon="📚",
    layout="centered"
)

# Estilização visual
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .abaco-header {
        background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .abaco-logo {
        width: 180px;
        margin-bottom: 15px;
        filter: brightness(0) invert(1);
    }
    .stButton>button {
        width: 100%;
        background-color: #134074;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0b2545;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("""
    <div class="abaco-header">
        <img src="https://colegioabaco.com.br/wp-content/themes/themecolegioabaco/images/colegio-abaco.png" class="abaco-logo">
        <h2>Portal de Envio Pedagógico</h2>
        <p style="margin: 0; color: #8da9c4; font-size: 15px;">Unificação de Redes Sociais • Curadoria Inteligente por IA</p>
    </div>
""", unsafe_allow_html=True)

# Função para criar uma pasta específica e subir as fotos lá dentro
def criar_pasta_e_subir_fotos(uploaded_files, unidade, folder_id, credentials_dict):
    try:
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=credentials)
        
        # 1. Cria o nome da pasta com a unidade e a data/hora atual
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_pasta_envio = f"{unidade} - {timestamp}"
        
        folder_metadata = {
            'name': nome_pasta_envio,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id]
        }
        
        # Cria a pasta no Google Drive
        pasta_criada = service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
        nova_pasta_id = pasta_criada.get('id')
        link_pasta = pasta_criada.get('webViewLink')
        
        # 2. Sobe cada arquivo enviado para dentro dessa nova pasta criada
        for file in uploaded_files:
            file_metadata = {
                'name': file.name,
                'parents': [nova_pasta_id]
            }
            media = MediaIoBaseUpload(
                io.BytesIO(file.getvalue()),
                mimetype=file.type,
                resumable=True
            )
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
        return link_pasta
    except Exception as e:
        return f"Erro ao criar pasta: {str(e)}"

# Configuração automática das Chaves via Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    sheetdb_url = st.secrets["SHEETDB_API_URL"]
    folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
    creds_dict = dict(st.secrets["google_credentials"])
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    with st.form("form_atividade"):
        unidade = st.selectbox(
            "Selecione a Unidade Escolar:",
            [
                "Unidade I - SBC (Educação Infantil / Fundamental I)", 
                "Unidade II - SBC (Fundamental II / Médio)", 
                "Unidade São Paulo / Ipiranga", 
                "Unidade São Paulo / Sumaré",
                "Unidade Mogi das Cruzes",
                "Unidade São Carlos"
            ]
        )
        
        uploaded_files = st.file_uploader(
            "Carregue as fotos da atividade (Selecione até 20 imagens):", 
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        relato = st.text_area(
            "Relato Pedagógico da Atividade:",
            placeholder="Ex: Os alunos participaram de um projeto no laboratório, desenvolvendo..."
        )
        
        submitted = st.form_submit_button("🚀 Enviar e Analisar com IA")

        if submitted:
            if uploaded_files and relato:
                if len(uploaded_files) > 20:
                    st.warning("⚠️ Você enviou mais de 20 fotos. Por favor, selecione no máximo 20 imagens por envio.")
                else:
                    with st.spinner(f"Processando {len(uploaded_files)} foto(s), criando pasta exclusiva e analisando com IA..."):
                        try:
                            # 1. Análise com a primeira imagem
                            primeira_imagem = Image.open(uploaded_files[0])
                            
                            prompt = f"""
                            Você é um assistente pedagógico especialista em marketing digital e curadoria de conteúdo para as redes sociais do Colégio Ábaco.
                            Analise a foto enviada e o relato pedagógico fornecido pelo professor para a unidade: {unidade}.
                            
                            Relato do professor: "{relato}"
                            
                            Responda estritamente seguindo esta estrutura em texto claro:
                            
                            **STATUS DA FOTO:** [Aprovada OU Rejeitada]
                            **MOTIVO:** [Explique em uma frase curta o porquê da aprovação ou rejeição técnica/pedagógica]
                            **LEGENDA SUGERIDA:** [Se aprovada, crie uma legenda cativante e profissional para o Instagram/Facebook do Colégio Ábaco, com emojis e 3 hashtags. Se rejeitada, escreva 'N/A']
                            """
                            
                            response = model.generate_content([primeira_imagem, prompt])
                            resposta_ia = response.text
                            
                            st.success("Análise concluída com sucesso!")
                            st.markdown("### 📊 Resultado da Curadoria:")
                            st.write(resposta_ia)
                            
                            # 2. Cria a pasta exclusiva no Drive e joga as fotos lá dentro
                            link_da_pasta_criada = criar_pasta_e_subir_fotos(uploaded_files, unidade, folder_id, creds_dict)
                            
                            status_aprovado = "Aprovada" if "Aprovada" in resposta_ia else "Rejeitada"
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                            
                            # 3. Registra os dados e o link da pasta na Planilha do Google
                            dados_para_planilha = {
                                "data": data_atual,
                                "unidade": unidade,
                                "relato": relato,
                                "status": status_aprovado,
                                "motivo": "Ver relatório gerado",
                                "legenda": resposta_ia,
                                "nome_arquivo_foto": link_da_pasta_criada
                            }
                            
                            requests.post(sheetdb_url, json=dados_para_planilha)
                            st.info("📁 Pasta exclusiva criada no Google Drive com as fotos, e link enviado automaticamente para a planilha do marketing!")
                            
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao processar: {e}")
            else:
                st.warning("⚠️ Por favor, envie pelo menos uma foto e preencha o relato pedagógico.")

except Exception as e:
    st.error("⚠️ Erro de configuração nas Secrets. Verifique as credenciais do Google Drive, Gemini e SheetDB.")
