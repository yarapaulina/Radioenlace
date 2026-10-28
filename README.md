# RadioLink Pro — Sistema de Cálculo e Otimização de Rádio Enlace com IA

Uma aplicação web moderna, de alta fidelidade e precisão matemática para projeto, dimensionamento e otimização assistida por Inteligência Artificial de enlaces de rádio ponto a ponto (PTP) e ponto-multiponto (PTMP).

---

## 🚀 Funcionalidades Principais

1. **Balanço de Potência Completo (Link Budget):**
   - **PIRE / EIRP:** Cálculo da Potência Isotrópica Radiada Equivalente com perdas em cabos e conectores.
   - **Atenuação no Espaço Livre (FSPL):** Modelo clássico de Friis para qualquer frequência (de 100 MHz a 100 GHz).
   - **Potência Recebida (RSL):** Nível de sinal exato no receptor com avaliação de sensibilidade.
   - **Margem de Desvanecimento (Fade Margin):** Classificação automática com alertas visuais (Crítico, Marginal, Viável, Excelente).

2. **Zonas de Fresnel e Perfil de Elevação Interativo:**
   - Cálculo contínuo do raio da **1ª Zona de Fresnel ($R_1$)** ao longo de todo o trajeto.
   - Verificação da folga crítica de **60% da 1ª Zona de Fresnel** (Recomendação ITU-R P.526).
   - Modelo de **Abaulamento e Curvatura da Terra** com Fator $K$ de refração atmosférica (padrão $K = 4/3$).
   - Gráfico dinâmico em **Canvas 2D** com crosshair interativo e tooltip em tempo real com cotas e folgas.
   - Cadastro e visualização de obstáculos (árvores, morros, prédios) no trajeto com detecção de obstrução.

3. **Modelos Climáticos e Atenuação Atmosférica (Normas ITU-R):**
   - **ITU-R P.838 & P.530:** Atenuação específica por chuva com suporte a polarização **Horizontal (H)** e **Vertical (V)** e taxas pluviométricas $R_{0.01}$ (ex: 42 mm/h para clima tropical).
   - **ITU-R P.676:** Absorção por gases atmosféricos (Oxigênio $O_2$ e Vapor d'Água $H_2O$), incluindo ressonância em 22.2 GHz e 60 GHz.

4. **Confiabilidade e Disponibilidade Anual:**
   - Modelo de desvanecimento por múltiplos percursos (**Vigants-Barnett / ITU-R P.530**).
   - Cálculo de disponibilidade percentual (ex: 99.99% ou 99.999% "5 noves").
   - Estimativa de tempo de queda acumulada anual em minutos e segundos por ano.

5. **Otimização Assistida por Inteligência Artificial:**
   - **Motor Multiobjetivo:** Dimensiona automaticamente ganhos de antenas parabólicas comerciais (0.3m a 1.8m), potência conduzida ideal e elevação necessária de torres.
   - **Checklist Técnico:** Gera lista de ações corretivas com análise de conformidade regulatória (ex: Resoluções da **ANATEL**).
   - **Aplicação em 1 Clique:** Carrega instantaneamente os parâmetros otimizados no formulário.

6. **Consultor Especialista em Telecomunicações (IA):**
   - **Motor Especialista Local (Offline):** Raciocínio heurístico detalhado de engenharia de RF sem necessidade de conexão externa.
   - **Integração com Google Gemini 3.8 Flash:** Suporte à chave de API para respostas contextuais expandidas e consultoria personalizada.

7. **Exportação de Relatórios Profissionais:**
   - **Memorial Técnico em PDF:** Documento pronto para apresentação técnica e homologação.
   - **Planilha CSV:** Exportação de todos os parâmetros de entrada, balanço e pontos do perfil de elevação.

---

## 🛠️ Como Executar a Aplicação

### 1. Pré-requisitos
- Python 3.10 ou superior.

### 2. Ativação do Ambiente Virtual e Dependências
```bash
# Entrar no diretório do projeto
cd Radioenlace

# Ativar o ambiente virtual existente
source .venv/bin/activate

# Caso queira reinstalar as dependências:
pip install -r requirements.txt
```

### 3. Iniciar o Servidor
Execute o script pronto:
```bash
./run.sh
```
Ou diretamente pelo Uvicorn:
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Acesse no seu navegador: **`http://localhost:8000`**

---

## 🧪 Testes Automatizados

Para executar a suíte completa de testes unitários e de integração:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v tests/
```

---

## 📁 Estrutura do Projeto

```
Radioenlace/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Endpoints FastAPI e rotas da API
│   ├── models.py                # Modelos Pydantic de validação
│   ├── core/
│   │   ├── __init__.py
│   │   ├── radio_math.py        # Fórmulas físicas e eletromagnéticas ITU-R
│   │   ├── optimizer.py         # Motor de otimização de antenas e torres
│   │   ├── ai_assistant.py      # Motor especialista local e Gemini 3.8 Flash
│   │   └── report_generator.py  # Geração de relatórios PDF e CSV
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Design System moderno, glassmorphism e temas
│   │   └── js/
│   │       ├── chart_renderer.js # Renderizador Canvas do perfil e zonas de Fresnel
│   │       └── app.js           # Gerenciamento de estado reativo e chamadas à API
│   └── templates/
│       └── index.html           # Interface do Dashboard
├── tests/
│   └── test_radio_math.py       # Testes unitários de RF e rotas
├── requirements.txt             # Dependências Python
├── run.sh                       # Script de inicialização facilitada
└── README.md                    # Documentação do projeto
```
# Radioenlace
# Radioenlace
