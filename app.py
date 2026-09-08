import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Portal Pedagógico - Colégio Ábaco",
    page_icon="📚",
    layout="centered"
)

# Estilização visual limpa e focada em rapidez
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
        padding: 12px;
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
        <h2>Envio de Atividades para Redes Sociais</h2>
        <p style="margin: 0; color: #8da9c4; font-size: 15px;">Colégio Ábaco • Envie suas mídias de forma rápida</p>
    </div>
""", unsafe_allow_html=True)

# Pasta interna de salvamento seguro
PASTA_INTERNA = "fotos_salvas"
if not os.path.exists(PASTA_INTERNA):
    os.makedirs(PASTA_INTERNA)

# Configuração das Chaves
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    sheetdb_url = st.secrets["SHEETDB_API_URL"]
    
    genai.configure(api_key=api_key)
    # Atualizado para o modelo atual suportado pela API
    model = genai.GenerativeModel('gemini-3.7-flash')
    
    with st.form("form_atividade", clear_on_submit=True):
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
        
        # Permitindo até 30 fotos
        uploaded_files = st.file_uploader(
            "Selecione as fotos da atividade (Até 30 imagens):", 
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )
        
        relato = st.text_area(
            "Relato Pedagógico (Conte brevemente como foi a atividade):",
            placeholder="Ex: Alunos do Infantil participaram de uma vivência de plantio..."
        )
        
        submitted = st.form_submit_button("🚀 Enviar Material para a Central")

        if submitted:
            if uploaded_files and relato:
                if len(uploaded_files) > 30:
                    st.warning("⚠️ O limite máximo é de 30 fotos por envio.")
                else:
                    with st.spinner("Enviando material com segurança para a central de marketing..."):
                        try:
                            # 1. Análise silenciosa pela IA
                            primeira_imagem = Image.open(uploaded_files[0])
                            
                            prompt = f"""
                            Você é um assistente pedagógico especialista em marketing digital e curadoria de conteúdo para as redes sociais do Colégio Ábaco.
                            Analise a foto enviada e o relato pedagógico fornecido pelo professor para a unidade: {unidade}.
                            
                            Relato do professor: "{relato}"
                            
                            Responda estritamente seguindo esta estrutura em texto claro:
                            
                            **STATUS DA FOTO:** [Aprovada OU Rejeitada]
                            **MOTIVO:** [Explique em uma frase curta o porquê da aprovação ou rejeição técnica]
                            **LEGENDA SUGERIDA:** [Se aprovada, crie uma legenda cativante e profissional para o Instagram/Facebook do Colégio Ábaco, com emojis e 3 hashtags. Se rejeitada, escreva 'N/A']
                            """
                            
                            response = model.generate_content([primeira_imagem, prompt])
                            resposta_ia = response.text
                            
                            # 2. Salvamento privado das fotos no servidor do app
                            nomes_arquivos_salvos = []
                            timestamp_lote = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            for idx, file in enumerate(uploaded_files):
                                nome_seguro = f"{timestamp_lote}_{idx}_{file.name}"
                                caminho_completo = os.path.join(PASTA_INTERNA, nome_seguro)
                                
                                with open(caminho_completo, "wb") as f:
                                    f.write(file.getbuffer())
                                
                                nomes_arquivos_salvos.append(nome_seguro)
                            
                            string_nomes = " | ".join(nomes_arquivos_salvos)
                            status_aprovado = "Aprovada" if "Aprovada" in resposta_ia else "Rejeitada"
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                            
                            # 3. Envio direto para a Planilha do Marketing via SheetDB
                            dados_para_planilha = {
                                "data": data_atual,
                                "unidade": unidade,
                                "relato": relato,
                                "status": status_aprovado,
                                "motivo": "Análise automatizada concluída",
                                "legenda": resposta_ia,
                                "nome_arquivo_foto": f"Arquivos salvos: {string_nomes}"
                            }
                            
                            requests.post(sheetdb_url, json=dados_para_planilha)
                            
                            st.success("✨ Material enviado com sucesso! A equipe de marketing já recebeu os arquivos e a sugestão de legenda na central.")
                            
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao processar o envio: {e}")
            else:
                st.warning("⚠️ Por favor, adicione pelo menos uma foto e preencha o relato pedagógico.")

except Exception as e:
    st.error("⚠️ Erro de configuração nas Secrets. Verifique as chaves do Gemini e do SheetDB.")
