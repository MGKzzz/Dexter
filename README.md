# DEXTER - Detecção e Censura

**Versão:** 0.2  
**Desenvolvido por:** MGKzzz

## Sobre o Projeto

O DEXTER é uma aplicação desktop desenvolvida em Python que realiza a detecção e censura automática de conteúdos sensíveis em imagens. Utilizando a biblioteca [NudeNet](https://github.com/notAI-tech/NudeNet) para identificar nudez, o software processa pastas de imagens e aplica censura quando necessário, preservando a privacidade do usuário e evitando a exposição a conteúdos explícitos.

### Principais Funcionalidades

- **Processamento em Lote:** Selecione uma pasta e processe todas as imagens suportadas (PNG, JPG, JPEG, WEBP, BMP, TIFF).
- **Detecção de Nudez:** Utiliza uma rede neural para detectar conteúdo sensível.
- **Censura Automática:** Aplica uma máscara de censura às imagens identificadas.
- **Interface Gráfica Intuitiva:** Desenvolvida com PySide6, a interface apresenta logs, barra de progresso e status de processamento.
- **Segurança e Privacidade:** Processa imagens de forma que o usuário não tenha contato direto com conteúdo sensível.
- **Registro Detalhado:** Logs para monitoramento e depuração do processamento.

## Pré-requisitos

- **Python 3.8+**  
- **Bibliotecas Python:**
  - PySide6
  - Pillow
  - NudeNet
  - OS
  - Sys
  - tempfile
  - traceback

## Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu_usuario/DEXTER.git
   cd DEXTER
2. **Execute o código**
