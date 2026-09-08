import streamlit as st
import google.generativeai as genai
from PIL import Image

# Configuração da página do aplicativo
st.set_page_config(
    page_title="Curadoria IA - Colégio Ábaco",
    page_icon="📚",
    layout="centered"
)

# Estilização visual com a identidade do Colégio Ábaco (Azul Escuro e Azul Claro)
st.markdown("""
    <style>
    /* Fundo geral sutil */
    .main {
        background-color: #f4f7f6;
    }
    
    /* Cabeçalho personalizado do Ábaco */
    .abaco-header {
        background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Força o logo azul original a ficar totalmente BRANCO no fundo escuro */
    .abaco-logo {
        width: 180px;
        margin-bottom: 15px;
        filter: brightness(0) invert(1);
    }

    /* Estilo dos botões */
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

# Cabeçalho Visual com Logo Branco e Cores do Ábaco
st.markdown("""
    <div class="abaco-header">
        <img src="https://colegioabaco.com.br/wp-content/themes/themecolegioabaco/images/colegio-abaco.png" class="abaco-logo">
        <h2>Portal de Envio Pedagógico</h2>
        <p style="margin: 0; color: #8da9c4; font-size: 15px;">Unificação de Redes Sociais • Curadoria Inteligente por IA</p>
    </div>
""", unsafe_allow_html=True)

# Configuração da Chave da API do Gemini
api_key = st.text_input("Insira sua chave da API do Google Gemini (AI Studio):", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    st.markdown("---")

    # Formulário de Envio
    with st.form("form_atividade"):
        unidade = st.selectbox(
            "Selecione a Unidade Escolar:",
            ["Unidade I - SBC (Educação Infantil / Fundamental I)", "Unidade II - SBC (Fundamental II / Médio)", "Unidade São Paulo / Ipiranga", "Unidade São Paulo / Sumaré"]
        )
        
        uploaded_file = st.file_uploader(
            "Carregue a foto da atividade (JPG ou PNG):", 
            type=["jpg", "jpeg", "png"]
        )
        
        relato = st.text_area(
            "Relato Pedagógico da Atividade:",
            placeholder="Ex: Os alunos do Fundamental participaram de um projeto no laboratório, desenvolvendo..."
        )
        
        submitted = st.form_submit_button("🚀 Enviar para Análise da IA")

        if submitted:
            if uploaded_file is not None and relato:
                with st.spinner("A IA do Ábaco está analisando a imagem e redigindo a legenda..."):
                    try:
                        image = Image.open(uploaded_file)
                        
                        prompt = f"""
                        Você é um assistente pedagógico especialista em marketing digital e curadoria de conteúdo para as redes sociais do Colégio Ábaco.
                        Analise a foto enviada e o relato pedagógico fornecido pelo professor.
                        
                        Relato do professor: "{relato}"
                        
                        Responda estritamente seguindo esta estrutura em texto claro:
                        
                        **STATUS DA FOTO:** [Aprovada OU Rejeitada]
                        **MOTIVO:** [Explique em uma frase curta o porquê da aprovação ou rejeição técnica/pedagógica da imagem, ex: Boa iluminação e foco excelente, ou foto escura/tremida]
                        **LEGENDA SUGERIDA:** [Se aprovada, crie uma legenda cativante, acolhedora e profissional para o Instagram/Facebook do Colégio Ábaco, destacando o aprendizado citado no relato, com emojis e 3 hashtags institucionais. Se rejeitada, escreva 'N/A']
                        """
                        
                        response = model.generate_content([image, prompt])
                        
                        st.success("Análise concluída com sucesso!")
                        st.markdown("### 📊 Resultado da Curadoria:")
                        st.write(response.text)
                        
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar com a IA: {e}")
            else:
                st.warning("⚠️ Por favor, envie uma foto e preencha o relato pedagógico antes de enviar.")
else:
    st.info("💡 Para iniciar os testes, insira sua chave gratuita da API do Gemini acima (disponível no [Google AI Studio](https://aistudio.google.com/)).")
