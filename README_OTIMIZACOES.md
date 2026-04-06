# Audio-Reactive Pattern Recognition Macro - Otimizações Técnicas v4.5

## 📋 Resumo das Melhorias Implementadas

### 1. **Otimização da Engine de Áudio (CPU)**
- **Pré-normalização**: Arquivo de referência normalizado uma única vez no carregamento
- **Média Móvel Exponencial**: Suavização do volume para evitar flutuações bruscas
- **Buffer Circular**: Análise de contexto com `deque` para processamento mais inteligente
- **Normalização Condicional**: Só normaliza quando necessário (evita divisão por zero)

### 2. **Device Discovery Cross-Platform Robusto**
- **Detecção por Plataforma**: Mapeamento específico para Linux, Windows e macOS
- **Fallback Inteligente**: 3 níveis de prioridade (monitor → mais canais → padrão)
- **Identificação de Host API**: WASAPI, PulseAudio, PipeWire, CoreAudio

### 3. **Thread-Safe UI Updates**
- **`self.after(0, ...)`**: Atualizações de UI sempre na thread principal
- **Prevenção de Race Conditions**: Evita crashes em sistemas multi-core

---

## 🎯 Análise: MFCC vs Cross-Correlation para Sons Percussivos

### **Cross-Correlation (Atual)**
**Vantagens:**
- ✅ Simples e direto para padrões temporais exatos
- ✅ Funciona bem quando o som é idêntico ao referência
- ✅ Baixa latência computacional
- ✅ Não requer extração de features complexas

**Desvantagens:**
- ❌ Sensível a variações de volume/timbre
- ❌ Não funciona bem com ruído de fundo
- ❌ Requer alinhamento temporal preciso
- ❌ Falso-positivos com sons similares

### **MFCC (Mel-Frequency Cepstral Coefficients)**
**Vantagens:**
- ✅ Robusto a variações de volume e timbre
- ✅ Foca nas características espectrais (não na forma de onda exata)
- ✅ Melhor para sons percussivos com harmônicos complexos
- ✅ Menos sensível a ruído de fundo
- ✅ Padrão da indústria para reconhecimento de áudio

**Desvantagens:**
- ❌ Mais complexo computacionalmente
- ❌ Requer mais memória (cálculo de FFT)
- ❌ Pode perder informações temporais finas
- ❌ Necessita de mais amostras para treinamento

### **Recomendação para o Seu Caso**

Para **gotas d'água em jogos** (sons curtos ~0.1-0.5s, percussivos, com harmônicos):

**🏆 HÍBRIDO RECOMENDADO:**
1. **Use Cross-Correlation como primeiro filtro** (rápido, baixo CPU)
2. **Se match_score > 0.3**, aplique MFCC como validação secundária
3. **Decisão final baseada em weighted score**: `final = 0.6*cross_corr + 0.4*mfcc_sim`

---

## 🔧 Implementação MFCC (Opcional - Para Maior Precisão)

Se quiser implementar MFCC, aqui está uma versão otimizada:

```python
# Adicionar imports
from scipy.signal import find_peaks
from scipy.spatial.distance import cosine

def extract_mfcc_features(signal, sr=16000, n_mfcc=13, n_fft=512, hop_length=160):
    """Extrai MFCC de forma otimizada para sons curtos"""
    # Pré-ênfase
    signal = np.append(signal, 0.0)  # Evitar problemas de borda
    signal = np.lfilter([1, -0.97], [1], signal)
    
    # FFT e espectro de potência
    magnitude = np.abs(np.fft.rfft(signal, n=n_fft))
    power_spec = magnitude ** 2
    
    # Filtros Mel (simplificado)
    n_mel = 40
    mel_filterbank = create_mel_filterbank(sr, n_fft, n_mel)
    mel_spec = np.dot(mel_filterbank, power_spec)
    
    # Log e DCT (apenas primeiros 13 coefficients)
    log_mel = np.log(mel_spec + 1e-10)
    mfcc = scipy.fft.dct(log_mel)[:n_mfcc]
    
    return mfcc

def create_mel_filterbank(sr, n_fft, n_mel):
    """Cria banco de filtros Mel (uma vez, reutiliza)"""
    # Implementação simplificada - na prática use librosa.filters.mel
    pass

def calculate_mfcc_similarity(mfcc1, mfcc2):
    """Calcula similaridade entre vetores MFCC"""
    # Cosseno de similaridade (1 = idêntico, 0 = ortogonal)
    similarity = 1 - cosine(mfcc1, mfcc2)
    return max(0, similarity)  # Garante valor entre 0-1
```

**Custo Computacional Estimado:**
- Cross-Correlation: ~0.5ms por bloco (4096 samples @ 16kHz)
- MFCC: ~2-3ms por bloco (depende do n_mfcc)
- **Híbrido**: ~1ms médio (só calcula MFCC se cross-corr > threshold)

---

## 📊 Calibração de Thresholds

### **Para Minimizar FPR (False Positive Rate):**

1. **Threshold de Volume**:
   - Comece com `threshold_vol = 1.0` (mais alto = menos falsos positivos)
   - Ajuste baseado no ruído ambiente do seu sistema

2. **Threshold de Match**:
   - `match_precision = 0.5` para sons muito específicos
   - `match_precision = 0.3` para sons mais genéricos

3. **Cooldown**:
   - `2.2s` atual está bom para gotas d'água
   - Aumente para `3-5s` se tiver muitos falsos positivos

### **Para Minimizar FNR (False Negative Rate):**

1. **Suavização (`alpha`)**:
   - `alpha = 0.05` para detecção mais sensível
   - `alpha = 0.2` para detecção mais rápida

2. **Blocksize**:
   - `4096` samples = 256ms @ 16kHz (bom equilíbrio)
   - `2048` samples = 128ms (mais responsivo, mais CPU)

---

## 🚀 Otimizações Adicionais Sugeridas

### **1. Detecção por Energia Relativa**
```python
def detect_by_energy_ratio(self, input_signal):
    """Detecta sons baseados na razão sinal/ruído"""
    # Calcula energia em bandas de frequência
    fft = np.abs(np.fft.rfft(input_signal))
    
    # Gotas d'água tipicamente têm pico em 2-5kHz
    high_freq_energy = np.mean(fft[1000:5000])  # 2-5kHz
    low_freq_energy = np.mean(fft[0:1000])      # 0-2kHz
    
    ratio = high_freq_energy / (low_freq_energy + 1e-9)
    return ratio > 3.0  # Threshold empírico
```

### **2. Validação por Duração**
```python
# Sons de gota são curtos (~100-500ms)
# Rejeita sons muito longos (>1s) ou muito curtos (<50ms)
def validate_duration(self, signal_duration):
    return 0.05 < signal_duration < 1.0
```

### **3. Machine Learning Leve (Opcional)**
```python
# Se tiver dataset grande (>100 amostras positivas/negativas)
# Pode treinar um classificador simples:
from sklearn.ensemble import RandomForestClassifier

# Features: [energy, zcr, spectral_centroid, mfcc_1-13]
# Treinar uma vez, usar em produção
```

---

## 🔍 Debug e Monitoramento

### **Logs Recomendados para Debug:**
```python
# Adicionar no callback:
if match_score > 0.2:  # Log tudo acima de 20%
    self.log(f"📊 DEBUG: Vol={vol_threshold:.2f} | Match={match_score:.3f} | "
             f"Energy={input_energy:.3f} | RefEnergy={self.ref_energy:.3f}")
```

### **Métricas de Performance:**
```python
# Adicionar no __init__:
self.stats = {
    'total_triggers': 0,
    'false_positives': 0,
    'false_negatives': 0,
    'avg_match_score': 0.0
}
```

---

## 📝 Checklist de Implantação

- [x] Otimizar normalização (pré-processar referência)
- [x] Implementar média móvel para volume
- [x] Device discovery cross-platform
- [x] Thread-safe UI updates
- [ ] **Opcional**: Implementar validação MFCC
- [ ] **Opcional**: Adicionar detecção por energia relativa
- [ ] Coletar mais amostras para calibração fina
- [ ] Testar em diferentes sistemas (Linux/Windows/macOS)
- [ ] Ajustar thresholds baseado no dataset coletado

---

## 🎯 Próximos Passos

1. **Curto Prazo (1-2 semanas)**:
   - Testar versão atual em produção
   - Coletar métricas de FPR/FNR
   - Ajustar thresholds baseado em dados reais

2. **Médio Prazo (1 mês)**:
   - Implementar validação MFCC opcional
   - Adicionar detecção por energia relativa
   - Criar sistema de "aprendizado contínuo"

3. **Longo Prazo (3+ meses)**:
   - Se dataset > 1000 amostras, treinar ML classifier
   - Otimizar para múltiplos sons simultâneos
   - Adicionar interface de configuração avançada

---

## 📚 Referências Técnicas

- **MFCC**: https://en.wikipedia.org/wiki/Mel-frequency_cepstrum
- **Cross-Correlation**: https://en.wikipedia.org/wiki/Cross-correlation
- **SoundDevice**: https://python-sounddevice.readthedocs.io/
- **Audio Feature Extraction**: https://librosa.org/doc/latest/feature.html

---

**Autor**: Claude Code Assistant  
**Data**: 2026-04-06  
**Versão**: v4.5 - Otimizada