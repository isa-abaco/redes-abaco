import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from datetime import datetime
import os
import zipfile
import io

# Configuração da página
st.set_page_config(
    page_title="Portal Pedagógico - Colégio Ábaco",
    page_icon="📚",
    layout="centered"
)

# Estilização visual limpa
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
        <h2>Portal de Envio Pedagógico</h2>
        <p style="margin: 0; color: #8da9c4; font-size: 15px;">Colégio Ábaco • Curadoria Inteligente</p>
    </div>
""", unsafe_allow_html=True)

# Pasta interna de salvamento seguro
PASTA_INTERNA = "fotos_salvas"
if not os.path.exists(PASTA_INTERNA):
    os.makedirs(PASTA_INTERNA)

# Configuração das Chaves via Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    sheetdb_url = st.secrets["SHEETDB_API_URL"]
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.7-flash')
    
    aba_professor, aba_marketing = st.tabs(["📝 Envio de Atividades", "🔒 Área Restrita (Marketing)"])
    
    with aba_professor:
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
                        # Feedback ultra-rápido para o professor não ficar esperando
                        with st.spinner("📤 Salvando e enviando para a central..."):
                            try:
                                # 1. Salvamento relâmpago das fotos no servidor
                                nomes_arquivos_salvos = []
                                timestamp_lote = datetime.now().strftime("%Y%m%d_%H%M%S")
                                
                                for idx, file in enumerate(uploaded_files):
                                    nome_seguro = f"{timestamp_lote}_{idx}_{file.name}"
                                    caminho_completo = os.path.join(PASTA_INTERNA, nome_seguro)
                                    
                                    with open(caminho_completo, "wb") as f:
                                        f.write(file.getbuffer())
                                    
                                    nomes_arquivos_salvos.append(nome_seguro)
                                
                                # 2. Análise leve com a IA usando apenas a primeira foto para gerar a legenda instantaneamente sem gargalo
                                primeira_imagem = Image.open(uploaded_files[0])
                                
                                prompt = f"""
                                Você é um assistente pedagógico especialista em marketing digital e curadoria de conteúdo para as redes sociais do Colégio Ábaco.
                                Analise a foto e o relato pedagógico fornecido pelo professor para a unidade: {unidade}.
                                
                                Relato do professor: "{relato}"
                                
                                Responda estritamente seguindo esta estrutura em texto claro:
                                
                                **STATUS DA FOTO:** [Aprovada OU Rejeitada]
                                **MOTIVO:** [Explique em uma frase curta o porquê da aprovação ou rejeição técnica]
                                **LEGENDA SUGERIDA:** [Se aprovada, crie uma legenda cativante e profissional para o Instagram/Facebook do Colégio Ábaco, com emojis e 3 hashtags. Se rejeitada, escreva 'N/A']
                                """
                                
                                response = model.generate_content([primeira_imagem, prompt])
                                resposta_ia = response.text
                                
                                string_nomes = " | ".join(nomes_arquivos_salvos)
                                status_aprovado = "Aprovada" if "Aprovada" in resposta_ia else "Rejeitada"
                                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
                                
                                # 3. Envio imediato para a Planilha do Google via SheetDB
                                payload_sheetdb = {
                                    "data": {
                                        "data": data_atual,
                                        "unidade": unidade,
                                        "relato": relato,
                                        "status": status_aprovado,
                                        "motivo": "Análise rápida concluída",
                                        "legenda": resposta_ia,
                                        "nome_arquivo_foto": f"Arquivos salvos: {string_nomes}"
                                    }
                                }
                                
                                requests.post(sheetdb_url, json=payload_sheetdb)
                                
                                st.success(f"✨ Sucesso! {len(uploaded_files)} foto(s) enviadas e encaminhadas para a equipe de marketing.")
                                
                            except Exception as e:
                                st.error(f"Ocorreu um erro ao processar o envio: {e}")
                else:
                    st.warning("⚠️ Por favor, adicione pelo menos uma foto e preencha o relato pedagógico.")

    with aba_marketing:
        st.subheader("Painel de Controle - Equipe de Marketing")
        st.write("Digite a senha da gestão para visualizar os envios e baixar os pacotes de fotos.")
        
        senha_digitada = st.text_input("Senha de Acesso:", type="password")
        SENHA_MESTRE = "abaco2026"
        
        if senha_digitada == SENHA_MESTRE:
            st.success("🔓 Acesso liberado!")
            
            try:
                response = requests.get(sheetdb_url)
                if response.status_code == 200:
                    dados_planilha = response.json()
                    
                    if dados_planilha:
                        st.markdown("---")
                        st.write(f"### Total de envios registrados: {len(dados_planilha)}")
                        
                        for i, linha in enumerate(reversed(dados_planilha)):
                            with st.expander(f"📌 {linha.get('data')} - {linha.get('unidade')} ({linha.get('status')})"):
                                st.write(f"**Relato Pedagógico:** {linha.get('relato')}")
                                st.markdown(f"**Sugestão de Legenda:**\n\n{linha.get('legenda')}")
                                
                                arquivos_str = linha.get('nome_arquivo_foto', '')
                                
                                if "Arquivos salvos:" in arquivos_str:
                                    lista_nomes = arquivos_str.replace("Arquivos salvos: ", "").split(" | ")
                                    
                                    st.write(f"**Fotos no Lote:** {len(lista_nomes)} imagem(ns)")
                                    
                                    zip_buffer = io.BytesIO()
                                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                                        for nome_arq in lista_nomes:
                                            caminho_arq = os.path.join(PASTA_INTERNA, nome_arq.strip())
                                            if os.path.exists(caminho_arq):
                                                zip_file.write(caminho_arq, arcname=nome_arq.strip())
                                    
                                    zip_buffer.seek(0)
                                    
                                    st.download_button(
                                        label=f"📥 Baixar Lote Completo de Fotos (.zip)",
                                        data=zip_buffer,
                                        file_name=f"fotos_lote_{i}.zip",
                                        mime="application/zip",
                                        key=f"download_zip_{i}"
                                    )
                                else:
                                    st.info("Nenhum arquivo de foto vinculado a este registro.")
                    else:
                        st.info("A planilha ainda não possui envios cadastrados.")
                else:
                    st.error("Não foi possível carregar os dados da planilha.")
            except Exception as e:
                st.error(f"Erro ao conectar com a base: {e}")
                
        elif senha_digitada != "":
            st.error("❌ Senha incorreta.")

except Exception as e:
    st.error(f"⚠️ Erro de configuração nas Secrets ou no sistema: {e}")
