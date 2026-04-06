# AI Macro Bridge - Universal Edition

Uma macro inteligente que detecta sons específicos do sistema e executa ações automáticas (cliques/teclas) usando IA de reconhecimento de áudio.

## 🚀 Funcionalidades

- **Detecção Inteligente de Áudio**: Reconhece padrões sonoros específicos usando correlação cruzada
- **Ações Automatizadas**: Click esquerdo, click direito, click duplo ou pressionar teclas
- **Interface Gráfica**: Painel completo com controles de sensibilidade e precisão
- **Modo Treino**: Capture e classifique sons para treinar a IA
- **Cross-Platform**: Funciona no Windows, Linux e macOS

## 📥 Instalação Rápida (Windows)

### Opção 1: Baixar Executável Pronto (Recomendado)

1. Vá para a seção **[Releases](https://github.com/SEU_USUARIO/SEU_REPOSITORIO/releases)** no GitHub
2. Baixe a versão mais recente (`MacroIA_Universal_vX.X.zip`)
3. Extraia o arquivo ZIP
4. Execute `MacroIA_Universal.exe`

### Opção 2: Build Manual (Para Desenvolvedores)

1. **Instale o Python 3.8+** em [python.org](https://www.python.org/downloads/)

2. **Clone o repositório**:
   ```bash
   git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
   cd SEU_REPOSITORIO
   ```

3. **Execute o script de build**:
   ```bash
   build_windows.bat
   ```

4. **O executável estará em**: `dist/MacroIA_Universal.exe`

## 🎮 Como Usar

### 1. Configuração Inicial

1. **Prepare o áudio de referência**:
   - Coloque um arquivo `referencia_base.wav` na pasta `dataset/`
   - Este arquivo deve conter o som que você quer detectar

2. **Execute o programa**:
   - Windows: `MacroIA_Universal.exe`
   - Linux/Mac: `python Macro.py`

### 2. Configurando a Macro

Na aba **⚙️ Ajustes IA**:

1. **Volume do Sistema**: Ajuste a sensibilidade de detecção
2. **Precisão da IA**: Defina o quão exato deve ser o match (32% padrão)
3. **Suavização**: Reduz flutuações na detecção
4. **Capturar Alvo**: Clique no botão e posicione o mouse onde quer que a macro clique (5 segundos)
5. **Selecionar Ação**: Escolha entre click esquerdo, direito, duplo ou tecla

### 3. Executando a Macro

1. Vá para aba **🚀 Execução**
2. Clique em **LIGAR MACRO IA**
3. A macro detectará sons similares ao arquivo de referência e executará a ação configurada

### 4. Modo Treino (Opcional)

Para melhorar a detecção:

1. Vá para aba **🧠 Treino**
2. Clique em **LIGAR CAPTURA**
3. Reproduza o som que deseja detectar
4. Clique em **👍 SALVAR POSITIVO** ou **👎 SALVAR NEGATIVO**
5. Repita para criar um dataset de treinamento

## 📁 Estrutura do Projeto

```
macroBridge/
├── Macro.py                 # Código principal
├── MacroIA_Universal.spec   # Configuração PyInstaller
├── requirements.txt         # Dependências Python
├── build_windows.bat       # Script de build Windows
├── dataset/                # Pasta de áudios
│   ├── referencia_base.wav # Áudio de referência (CRIAR ESTE ARQUIVO)
│   ├── positivo/           # Amostras positivas
│   └── negativo/           # Amostras negativas
└── modelo/                 # Modelos salvos (futuro)
```

## ⚙️ Requisitos do Sistema

### Windows
- **Windows 10/11** (testado)
- **Python 3.8+** (para build manual)
- **Stereo Mix habilitado** (para capturar áudio do sistema)

### Linux
- **Python 3.8+**
- **PulseAudio ou PipeWire**
- **pacmd ou pactl** para loopback

### macOS
- **Python 3.8+**
- **BlackHole ou Aggregate Device** para loopback

## 🔧 Dependências

```txt
customtkinter>=5.2.0
pyautogui>=0.9.54
sounddevice>=0.4.6
numpy>=1.24.0
scipy>=1.10.0
pyinstaller>=6.0.0
```

## 🛠️ Build para Outras Plataformas

### Linux
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name="MacroIA_Universal" --add-data "dataset:dataset" Macro.py
```

### macOS
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name="MacroIA_Universal" --add-data "dataset:dataset" Macro.py
```

## ⚠️ Problemas Comuns no Windows

### 1. "Stereo Mix não encontrado"
- Vá em **Configurações de Som** → **Painel de Controle de Som**
- Abra **Gravação** → Clique direito → **Mostrar Dispositivos Desabilitados**
- Habilite **Stereo Mix**

### 2. "Acesso negado ao controlar mouse"
- Execute o programa como **Administrador**
- Ou ajuste as permissões de acessibilidade

### 3. Antivírus bloqueia o .exe
- É um falso positivo comum do PyInstaller
- Adicione uma exceção no antivírus
- Ou faça build manual seguindo as instruções

## 📄 Licença

MIT License - Sinta-se livre para usar e modificar.

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: Abra uma issue no GitHub
- **Discord**: [Seu link do Discord]
- **Email**: [seu-email@exemplo.com]

---

**Desenvolvido com ❤️ por [Seu Nome]**