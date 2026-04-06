import customtkinter as ctk
import pyautogui
import sounddevice as sd
import numpy as np
import threading
import time
import os
import sys
from scipy.io.wavfile import write, read
from scipy.signal import correlate
from collections import deque
import platform

# --- CONFIGURAÇÕES DE EMULAÇÃO ---
pyautogui.MINIMUM_DURATION = 0.1 
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = False

class MacroADS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Macro Bridge - Universal Edition v4.5")
        self.geometry("750x900")
        
        # Localização Base
        self.base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

        # Variáveis de Controle
        self.coords = (0, 0) 
        self.is_running = False      
        self.is_training = False     
        self.fs = 16000
        self.threshold_vol = 0.5    # Sensibilidade de Volume
        self.match_precision = 0.32  # Precisão da IA
        self.device_index = None    # Detectado automaticamente
        
        # Variáveis de Ação (Macro Roblox)
        self.action_type = "click"  # "click", "key", "double_click"
        self.action_key = "e"  # Tecla para pressionar (padrão: E)
        self.click_button = "left"  # "left", "right", "middle"
        
        self.ref_data = None
        self.ref_data_normalized = None  # Pré-normalizado para performance
        self.last_audio_data = None
        self.last_action_time = 0
        
        # Otimização de Performance
        self.audio_buffer = deque(maxlen=5)  # Buffer circular para análise contínua
        self.running_avg_power = 0.0  # Média móvel para detecção mais suave
        self.alpha = 0.1  # Fator de suavização (0.1 = 10% novo, 90% antigo)

        # Caminhos e Pastas
        self.caminho_dataset = os.path.join(self.base_dir, "dataset")
        self.ref_path = os.path.join(self.caminho_dataset, "referencia_base.wav")
        for p in ["positivo", "negativo"]:
            os.makedirs(os.path.join(self.caminho_dataset, p), exist_ok=True)

        self.setup_ui()
        self.detectar_audio_sistema()
        self.carregar_assinatura_base()

    def detectar_audio_sistema(self):
        """Varre os dispositivos de forma robusta e cross-platform"""
        try:
            devices = sd.query_devices()
            self.log("🔍 Escaneando hardware de áudio...")
            
            # Mapeamento de palavras-chave por plataforma
            platform_keywords = {
                'Linux': ['monitor', 'loopback', 'pulse', 'pipewire', 'alsa_output'],
                'Windows': ['stereo mix', 'mistura estéreo', 'loopback', 'wasapi', 'wave out'],
                'Darwin': ['aggregate', 'multi-output', 'loopback', 'blackhole']
            }
            
            current_platform = platform.system()
            keywords = platform_keywords.get(current_platform, [])
            
            # Prioridade 1: Dispositivos de Monitoramento Específicos da Plataforma
            for i, dev in enumerate(devices):
                name = dev['name'].lower()
                hostapi = sd.query_hostapis()[dev['hostapi']]['name'].lower()
                
                # Verifica se é dispositivo de entrada com canais disponíveis
                if dev['max_input_channels'] > 0:
                    # Combina palavras-chave da plataforma + termos genéricos
                    all_keywords = keywords + ['monitor', 'loopback', 'stereo mix', 'mistura estéreo']
                    
                    if any(keyword in name for keyword in all_keywords):
                        self.device_index = i
                        self.log(f"✅ Áudio Interno Detectado: {dev['name']} (API: {hostapi})")
                        return

            # Prioridade 2: Dispositivo com maior número de canais de entrada (provável dispositivo de saída em loopback)
            max_channels = 0
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > max_channels:
                    max_channels = dev['max_input_channels']
                    self.device_index = i
                    
            if self.device_index is not None:
                self.log(f"⚠️ Monitor não achado. Usando dispositivo com mais canais: {devices[self.device_index]['name']}")
            else:
                # Prioridade 3: Dispositivo padrão do sistema
                self.device_index = sd.default.device[0]
                self.log("⚠️ Usando entrada padrão do sistema (pode ser microfone).")
                
        except Exception as e:
            self.log(f"❌ Erro ao acessar som: {e}")
            self.device_index = None

    def carregar_assinatura_base(self):
        """Carrega e pré-processa o arquivo de referência para otimização"""
        if os.path.exists(self.ref_path):
            try:
                samplerate, data = read(self.ref_path)
                
                # Se o sample rate for diferente, resample para 16000Hz
                if samplerate != self.fs:
                    from scipy.signal import resample
                    num_samples = int(len(data) * self.fs / samplerate)
                    data = resample(data, num_samples).astype(np.float32)
                    self.log(f"🔄 Resampled de {samplerate}Hz para {self.fs}Hz")
                else:
                    data = data.astype(np.float32)
                
                # Converte para float32 e normaliza uma única vez
                self.ref_data = data
                self.ref_data_normalized = self.ref_data / (np.max(np.abs(self.ref_data)) + 1e-9)
                
                # Calcula energia de referência para normalização relativa
                self.ref_energy = np.sqrt(np.mean(self.ref_data_normalized**2))
                
                self.log(f"🧠 IA: Assinatura carregada (SR={self.fs}, {len(self.ref_data)/self.fs:.2f}s, energia: {self.ref_energy:.3f})")
                
                # Validação básica do arquivo
                if len(self.ref_data) < 100:
                    self.log("⚠️ Arquivo de referência muito curto!")
                    
            except Exception as e:
                self.log(f"❌ Erro ao processar arquivo base: {e}")
        else:
            self.log("⚠️ Arquivo de referência não encontrado. Crie um arquivo 'referencia_base.wav' no dataset.")

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_macro = self.tabview.add("🚀 Execução")
        self.tab_config = self.tabview.add("⚙️ Ajustes IA")
        self.tab_treino = self.tabview.add("🧠 Treino")

        # --- ABA EXECUÇÃO ---
        self.btn_run = ctk.CTkButton(self.tab_macro, text="LIGAR MACRO IA", fg_color="#27ae60", height=60, command=self.toggle_macro)
        self.btn_run.pack(pady=20, fill="x", padx=60)
        self.log_box = ctk.CTkTextbox(self.tab_macro, height=400)
        self.log_box.pack(pady=10, padx=40, fill="x")

        # --- ABA AJUSTES ---
        ctk.CTkLabel(self.tab_config, text="1. VOLUME DO SISTEMA (SENSIBILIDADE)", font=("Roboto", 14, "bold")).pack(pady=10)
        self.slider_vol = ctk.CTkSlider(self.tab_config, from_=0.1, to=5.0, command=self.update_vol)
        self.slider_vol.set(self.threshold_vol)
        self.slider_vol.pack()
        self.lbl_vol = ctk.CTkLabel(self.tab_config, text=f"Corte: {self.threshold_vol}")
        self.lbl_vol.pack()

        ctk.CTkLabel(self.tab_config, text="2. PRECISÃO DA IA (MATCH)", font=("Roboto", 14, "bold")).pack(pady=15)
        self.slider_match = ctk.CTkSlider(self.tab_config, from_=0.1, to=1.0, command=self.update_match)
        self.slider_match.set(self.match_precision)
        self.slider_match.pack()
        self.lbl_match = ctk.CTkLabel(self.tab_config, text=f"Exigência: {int(self.match_precision*100)}%")
        self.lbl_match.pack()
        
        ctk.CTkLabel(self.tab_config, text="3. SUAVIZAÇÃO (ANTI-FLUTUAÇÃO)", font=("Roboto", 14, "bold")).pack(pady=15)
        self.slider_smooth = ctk.CTkSlider(self.tab_config, from_=0.01, to=0.5, command=self.update_smooth)
        self.slider_smooth.set(self.alpha)
        self.slider_smooth.pack()
        self.lbl_smooth = ctk.CTkLabel(self.tab_config, text=f"Fator: {self.alpha:.2f}")
        self.lbl_smooth.pack()

        self.btn_pos = ctk.CTkButton(self.tab_config, text="Capturar Alvo (5s)", command=self.capturar_posicao)
        self.btn_pos.pack(pady=10)
        
        # --- CONFIGURAÇÃO DE AÇÃO (ROBLOX) ---
        ctk.CTkLabel(self.tab_config, text="4. AÇÃO AO DETECTAR SOM", font=("Roboto", 14, "bold")).pack(pady=15)
        
        # Tipo de ação
        self.action_var = ctk.StringVar(value="click")
        self.action_menu = ctk.CTkOptionMenu(
            self.tab_config, 
            values=["Click Esquerdo", "Click Direito", "Click Duplo", "Tecla (E)", "Tecla Personalizada"],
            variable=self.action_var,
            command=self.update_action_type
        )
        self.action_menu.pack(pady=5)
        
        # Campo para tecla personalizada (inicialmente escondido)
        self.key_entry_frame = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        self.key_entry = ctk.CTkEntry(self.key_entry_frame, width=100, placeholder_text="Tecla")
        self.key_entry.insert(0, "e")
        self.key_entry.pack(side="left", padx=5)
        self.key_entry_label = ctk.CTkLabel(self.key_entry_frame, text="Tecla para pressionar")
        self.key_entry_label.pack(side="left", padx=5)
        self.key_entry_frame.pack(pady=5)
        self.key_entry_frame.pack_forget()  # Esconde inicialmente
        
        # Label de status da ação
        self.lbl_action = ctk.CTkLabel(self.tab_config, text="Ação: Click Esquerdo em " + str(self.coords), text_color="#3498db")
        self.lbl_action.pack(pady=5)

        # --- ABA TREINO ---
        self.btn_train = ctk.CTkButton(self.tab_treino, text="LIGAR CAPTURA", fg_color="#e67e22", command=self.toggle_train)
        self.btn_train.pack(pady=20, fill="x", padx=60)
        self.btn_save_pos = ctk.CTkButton(self.tab_treino, text="👍 SALVAR POSITIVO", fg_color="#27ae60", state="disabled", command=lambda: self.salvar_amostra("positivo"))
        self.btn_save_pos.pack(pady=10, fill="x", padx=100)
        self.btn_save_neg = ctk.CTkButton(self.tab_treino, text="👎 SALVAR NEGATIVO", fg_color="#c0392b", state="disabled", command=lambda: self.salvar_amostra("negativo"))
        self.btn_save_neg.pack(pady=5, fill="x", padx=100)

    def log(self, msg):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")

    def update_vol(self, v):
        self.threshold_vol = round(float(v), 2)
        self.lbl_vol.configure(text=f"Corte: {self.threshold_vol}")

    def update_match(self, v):
        self.match_precision = float(v)
        self.lbl_match.configure(text=f"Exigência: {int(self.match_precision*100)}%")
    
    def update_smooth(self, v):
        self.alpha = round(float(v), 3)
        self.lbl_smooth.configure(text=f"Fator: {self.alpha:.3f}")

    def update_action_type(self, selection):
        """Atualiza o type de ação baseado na seleção do menu"""
        if selection == "Click Esquerdo":
            self.action_type = "click"
            self.click_button = "left"
            self.key_entry_frame.pack_forget()
        elif selection == "Click Direito":
            self.action_type = "click"
            self.click_button = "right"
            self.key_entry_frame.pack_forget()
        elif selection == "Click Duplo":
            self.action_type = "double_click"
            self.key_entry_frame.pack_forget()
        elif selection == "Tecla (E)":
            self.action_type = "key"
            self.action_key = "e"
            self.key_entry_frame.pack(pady=5)
        elif selection == "Tecla Personalizada":
            self.action_type = "key"
            self.action_key = self.key_entry.get().lower()
            self.key_entry_frame.pack(pady=5)
        
        # Atualiza label de status
        self.lbl_action.configure(text=f"Ação: {selection} em {self.coords}")

    def capturar_posicao(self):
        self.btn_pos.configure(state="disabled", text="Aguarde...")
        def t():
            time.sleep(5)
            self.coords = pyautogui.position()
            self.btn_pos.configure(text=f"✅ Alvo: {self.coords}", state="normal")
        threading.Thread(target=t, daemon=True).start()

    def toggle_macro(self):
        self.is_running = not self.is_running
        if self.is_running: 
            self.is_training = False
            self.running_avg_power = 0.0  # Reset média móvel
            self.btn_run.configure(text="⏹️ PARAR MACRO IA", fg_color="#c0392b")
            self.log("🚀 Macro IA iniciada...")
            threading.Thread(target=self.audio_engine, daemon=True).start()
        else:
            self.btn_run.configure(text="🚀 LIGAR MACRO IA", fg_color="#27ae60")
            self.log("⏹️ Macro IA parada.")

    def toggle_train(self):
        self.is_training = not self.is_training
        if self.is_training: 
            self.is_running = False
            self.running_avg_power = 0.0  # Reset média móvel
            self.btn_train.configure(text="⏹️ PARAR CAPTURA", fg_color="#e74c3c")
            self.log("🧠 Modo treino iniciado...")
            threading.Thread(target=self.audio_engine, daemon=True).start()
        else:
            self.btn_train.configure(text="🧠 LIGAR CAPTURA", fg_color="#e67e22")
            self.log("⏹️ Modo treino parado.")

    def normalizacao_eficiente(self, signal):
        """Normalização otimizada que evita picos de CPU"""
        # Usa máximo absoluto apenas se necessário
        max_val = np.max(np.abs(signal))
        if max_val > 1e-9:
            return signal / max_val
        return signal

    def calcular_match_score_otimizado(self, input_signal):
        """Calcula score de similaridade de forma otimizada"""
        if self.ref_data_normalized is None:
            self.log("⚠️ ref_data_normalized é None!")
            return 0.0
            
        # Garante que os sinais são 1D
        input_1d = input_signal.flatten().astype(np.float32)
        ref_1d = self.ref_data_normalized.flatten().astype(np.float32)
        
        # Debug: verifica tamanhos
        # self.log(f"Debug: input_len={len(input_1d)}, ref_len={len(ref_1d)}")
        
        # Normaliza o input
        input_norm = self.normalizacao_eficiente(input_1d)
        
        # Pega o tamanho do mais curto para comparação
        min_len = min(len(input_norm), len(ref_1d))
        if min_len < 100:  # Muito curto para comparação significativa
            # self.log(f"⚠️ min_len={min_len} muito curto!")
            return 0.0
        
        # Corta ambos para o mesmo tamanho
        input_cut = input_norm[:min_len]
        ref_cut = ref_1d[:min_len]
        
        # Cross-correlation
        corr = correlate(input_cut, ref_cut, mode='full')
        
        if len(corr) == 0:
            return 0.0
        
        # Normaliza pelo produto das energias (coeficiente de correlação normalizado)
        input_energy = np.sqrt(np.sum(input_cut**2))
        ref_energy_val = np.sqrt(np.sum(ref_cut**2))
        
        if input_energy < 1e-9 or ref_energy_val < 1e-9:
            # self.log(f"⚠️ Energia muito baixa: input={input_energy}, ref={ref_energy_val}")
            return 0.0
        
        # Pico da correlação normalizado
        max_corr = np.max(np.abs(corr))
        normalized_corr = max_corr / (input_energy * ref_energy_val)
        
        # Debug
        # self.log(f"Debug: max_corr={max_corr:.4f}, input_e={input_energy:.4f}, ref_e={ref_energy_val:.4f}, score={normalized_corr:.4f}")
        
        # Retorna valor entre 0 e 1
        return min(max(normalized_corr, 0.0), 1.0)

    def audio_engine(self):
        """Engine de áudio otimizada com processamento eficiente"""
        process_count = 0
        # Variáveis para detecção de início/fim do som (apenas modo treino)
        sound_started = False
        sound_start_time = 0
        sound_detected = False
        buttons_activated = False  # Controle para não ativar botões múltiplas vezes
        noise_floor = 0.0  # Nível de ruído de fundo
        
        def callback(indata, frames, t_info, status):
            nonlocal process_count, sound_started, sound_start_time, sound_detected, buttons_activated, noise_floor
            process_count += 1
            
            # Cálculo de volume com média móvel para suavização
            current_power = np.sqrt(np.mean(indata**2)) * 10
            
            # MODO TREINO: detecção de som completo (início → fim) → ATIVA BOTÕES
            if self.is_training:
                # Atualiza média móvel para detecção
                self.running_avg_power = (1 - self.alpha) * self.running_avg_power + self.alpha * current_power
                
                # Calcula ruído de fundo (média dos últimos valores baixos)
                if current_power < self.threshold_vol * 0.3:
                    noise_floor = 0.95 * noise_floor + 0.05 * current_power
                
                # Detecção de início de som (depois de um período de silêncio)
                if not sound_started:
                    # Som deve ser SIGNIFICATIVAMENTE acima do ruído de fundo E do threshold
                    if current_power > self.threshold_vol and current_power > noise_floor * 3:
                        # Verifica se passou tempo suficiente desde o último som
                        if time.time() - sound_start_time > 1.0:  # 1 segundo de silêncio antes
                            sound_started = True
                            sound_start_time = time.time()
                            sound_detected = False
                            buttons_activated = False
                            self.log(f"🔊 Som detectado: {current_power:.2f} (ruído: {noise_floor:.2f})")
                
                # Detecção de fim de som (som deve cair para nível de ruído)
                elif sound_started and current_power < max(self.threshold_vol * 0.3, noise_floor * 2):
                    sound_duration = time.time() - sound_start_time
                    # Só considera válido se durou entre 100ms e 3s (som real de gota)
                    if 0.1 < sound_duration < 3.0:
                        # Calcula match score com a referência (se existir)
                        input_signal = indata.flatten().astype(np.float32)
                        match_score = self.calcular_match_score_otimizado(input_signal)
                        
                        # Só ativa botões se tiver match significativo com a referência
                        # Ou se não tiver referência carregada (primeiro treino)
                        if self.ref_data_normalized is None or match_score > self.match_precision * 0.5:
                            sound_detected = True
                            sound_started = False
                            # Ativa botões apenas uma vez
                            if not buttons_activated:
                                self.last_audio_data = np.copy(indata)
                                self.after(0, lambda: self.btn_save_pos.configure(state="normal"))
                                self.after(0, lambda: self.btn_save_neg.configure(state="normal"))
                                buttons_activated = True
                                self.log(f"✅ Som capturado! Match: {int(match_score*100)}% | Duração: {sound_duration:.2f}s. Clique em 👍 ou 👎")
                        else:
                            # Som detectado mas não parece com a referência
                            sound_started = False
                            self.log(f"⚠️ Som não corresponde à referência (match: {int(match_score*100)}%)")
                    else:
                        # Som inválido (muito curto ou muito longo)
                        sound_started = False
                        if sound_duration <= 0.1:
                            self.log(f"⚠️ Som muito curto ({sound_duration:.3f}s), ignorado")
                        else:
                            self.log(f"⚠️ Som muito longo ({sound_duration:.1f}s), ignorado")
            
            # MODO EXECUÇÃO: detecção por threshold + cooldown → EXECUTA CLIQUES
            elif self.is_running:
                # IMPORTANTE: No modo execução, NUNCA ativa botões de treino
                self.running_avg_power = (1 - self.alpha) * self.running_avg_power + self.alpha * current_power
                vol_threshold = max(self.running_avg_power, current_power)
                
                if vol_threshold > self.threshold_vol and (time.time() - self.last_action_time) > 2.2:
                    # Processamento IA otimizado
                    input_signal = indata.flatten().astype(np.float32)
                    
                    # Adiciona ao buffer circular para análise de contexto
                    self.audio_buffer.append(input_signal.copy())
                    
                    match_score = self.calcular_match_score_otimizado(input_signal)

                    if match_score > self.match_precision:
                        self.last_action_time = time.time()
                        self.log(f"🎯 Match: {int(match_score*100)}% | Vol: {round(vol_threshold,2)} | Avg: {round(self.running_avg_power,2)}")
                        threading.Thread(target=self.clicar, daemon=True).start()

        # Inicia a captura usando o dispositivo detectado automaticamente
        if self.device_index is None:
            self.log("❌ Nenhum dispositivo de áudio disponível!")
            return
            
        try:
            with sd.InputStream(device=self.device_index, callback=callback, channels=1, 
                              samplerate=self.fs, blocksize=4096, latency='low'):
                self.log(f"🎙️ Capturando áudio (device {self.device_index}, blocksize=4096)")
                while self.is_running or self.is_training:
                    sd.sleep(100)
        except Exception as e:
            self.log(f"❌ Erro na captura de áudio: {e}")

    def clicar(self):
        x, y = self.coords
        if x == 0 and self.action_type == "click": return  # Só retorna se for click e não tiver coords
        
        try:
            if self.action_type == "click":
                # Click simples na coordenada
                pyautogui.moveTo(x, y, duration=0.1)
                pyautogui.click(button=self.click_button)
            elif self.action_type == "double_click":
                # Click duplo na coordenada
                pyautogui.moveTo(x, y, duration=0.1)
                pyautogui.click(button="left")
                time.sleep(0.1)
                pyautogui.click(button="left")
            elif self.action_type == "key":
                # Pressiona tecla (sem mover mouse)
                pyautogui.press(self.action_key)
        except Exception as e:
            self.log(f"⚠️ Erro na ação: {e}")

    def salvar_amostra(self, tipo):
        if self.last_audio_data is not None:
            path = os.path.join(self.caminho_dataset, tipo, f"sample_{int(time.time())}.wav")
            norm = self.normalizacao_eficiente(self.last_audio_data)
            write(path, self.fs, (norm * 32767).astype(np.int16))
            self.log(f"💾 IA Aprendeu ({tipo})")
            # Limpa o áudio salvo para evitar reutilização
            self.last_audio_data = None
            # Atualiza UI de forma thread-safe
            self.after(0, lambda: self.btn_save_pos.configure(state="disabled"))
            self.after(0, lambda: self.btn_save_neg.configure(state="disabled"))
            self.log("🔄 Pronto para próximo som...")

if __name__ == "__main__":
    app = MacroADS()
    app.mainloop()