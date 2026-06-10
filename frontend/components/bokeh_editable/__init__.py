"""
Componente Streamlit para Bokeh com comunicação bidirecional.
Usa components.html() + localStorage + streamlit_js_eval para capturar eventos.
"""
import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
from bokeh.resources import CDN
import json
import sys
import importlib.util


print(
    "[BokehEditable][BOOT] "
    f"python={sys.executable} "
    f"streamlit_js_eval={importlib.util.find_spec('streamlit_js_eval')}"
)


def bokeh_editable(
    bokeh_figure,
    height: int = 1780,
    key: str = None,
    enable_storage_monitor: bool = True,
) -> list:
    """
    Renderiza um gráfico Bokeh com monitoramento de mudanças nos DataSources.
    Quando o usuário arrasta pontos, os novos valores são salvos no localStorage
    e podem ser lidos pelo Python via get_bokeh_updates().
    
    Args:
        bokeh_figure: O objeto Bokeh (figure ou layout) a ser renderizado
        height: Altura do componente em pixels
        key: Chave única do Streamlit para este componente
        enable_storage_monitor: Se True, monitora DataSources e escreve no localStorage.
            Em telas que já escrevem localStorage via callbacks próprios, use False para
            evitar concorrência de escrita (single-writer).
    
    Returns:
        None (valores são lidos via get_bokeh_updates())
    """
    storage_key = f"bokeh_update_{key or 'default'}"
    
    # Gera o HTML completo do Bokeh
    html_content = file_html(bokeh_figure, CDN, "Bokeh Chart")
    
    # JavaScript para monitorar mudanças e salvar no localStorage
    custom_js = '''
    <style>
        #bokeh-status {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 128, 0, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 9999;
            display: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
    </style>
    <div id="bokeh-status"></div>
    <script>
    (function() {
        const STORAGE_KEY = ''' + json.dumps(storage_key) + ''';
        const ENABLE_STORAGE_MONITOR = ''' + json.dumps(enable_storage_monitor) + ''';
        const statusDiv = document.getElementById('bokeh-status');
        
        function showStatus(msg) {
            statusDiv.textContent = msg;
            statusDiv.style.display = 'block';
            setTimeout(() => { statusDiv.style.display = 'none'; }, 2000);
        }
        
        function waitForBokeh(callback, maxWait) {
            const startTime = Date.now();
            const check = () => {
                if (typeof Bokeh !== 'undefined' && Bokeh.documents && Bokeh.documents.length > 0) {
                    callback();
                } else if (Date.now() - startTime < maxWait) {
                    setTimeout(check, 100);
                }
            };
            check();
        }
        
        waitForBokeh(function() {
            console.log('[BokehEditable] Configurando listeners...');
            
            const doc = Bokeh.documents[0];
            if (!doc) return;
            
            const allModels = doc._all_models;
            let debounceTimer = null;
            let lastSentData = null;
            
            function saveToStorage(yValues) {
                if (!ENABLE_STORAGE_MONITOR) return;
                const dataStr = JSON.stringify(yValues);
                if (dataStr === lastSentData) return;
                lastSentData = dataStr;
                
                // Salva no localStorage do parent (Streamlit)
                try {
                    window.parent.localStorage.setItem(STORAGE_KEY, dataStr);
                    window.parent.localStorage.setItem(STORAGE_KEY + '_timestamp', Date.now().toString());
                    console.log('[BokehEditable] Salvo no localStorage:', yValues);
                    showStatus('✓ Dados prontos para aplicar');
                } catch(e) {
                    console.error('[BokehEditable] Erro ao salvar:', e);
                }
            }
            
            // Encontra o ColumnDataSource do gráfico (src_ajs - com 12 valores de y)
            let graphSource = null;
            let tableSource = null;

            function extractGraphY() {
                if (graphSource && graphSource.data && graphSource.data.y && graphSource.data.y.length === 12) {
                    return Array.from(graphSource.data.y).map(v =>
                        Number.isFinite(v) ? parseFloat(v.toFixed(2)) : 0
                    );
                }
                return null;
            }
            
            allModels.forEach((model, id) => {
                if (model.type === 'ColumnDataSource') {
                    const isAjustadaPrincipal = (model.name === 'src_ajs_main') || (model.data && model.data.y_br && model.data.y && model.data.y.length === 12);
                    if (model.data && model.data.y && model.data.y.length === 12) {
                        if (isAjustadaPrincipal) {
                            graphSource = model;
                        }
                        console.log('[BokehEditable] Monitorando gráfico:', model.name || model.id);
                        
                        model.connect(model.properties.data.change, () => {
                            if (!ENABLE_STORAGE_MONITOR) return;
                            const data = model.data;
                            if (data && data.y && data.y.length === 12) {
                                const yValues = Array.from(data.y).map(v => 
                                    Number.isFinite(v) ? parseFloat(v.toFixed(2)) : 0
                                );
                                
                                if (debounceTimer) clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(() => {
                                    console.log('[BokehEditable] Gráfico mudou, salvando:', yValues);
                                    saveToStorage(yValues);
                                }, 300);
                            }
                        });
                    }
                    // Identifica fontes de tabela histórica (campos Ajuste_/Ajustada_ por ano)
                    const keys = model.data ? Object.keys(model.data) : [];
                    const isHistorica = keys.some(k => k.startsWith('Ajuste_') || k.startsWith('Ajustada_'));
                    if (model.data && (isHistorica || (model.data.Ajustada && model.data.Ajustada.length >= 12))) {
                        tableSource = model;
                        console.log('[BokehEditable] Monitorando tabela:', model.name || model.id);
                        
                        // Monitora mudanças na tabela também
                        model.connect(model.properties.data.change, () => {
                            if (!ENABLE_STORAGE_MONITOR) return;
                            const yValues = extractGraphY();
                            if (!yValues) return;

                            if (debounceTimer) clearTimeout(debounceTimer);
                            debounceTimer = setTimeout(() => {
                                saveToStorage(yValues);
                                console.log('[BokehEditable] Tabela histórica editada, sync via gráfico:', yValues.slice(0,3));
                            }, 300);
                        });
                    }
                }
            });
            
            console.log('[BokehEditable] Pronto! Edite a coluna Ajustada com clique duplo.');
        }, 10000);
    })();
    </script>
    '''
    
    # Insere o JavaScript antes do </body>
    html_with_js = html_content.replace('</body>', custom_js + '</body>')
    
    # Renderiza o HTML (scrolling=False para evitar reruns desnecessários)
    components.html(html_with_js, height=height, scrolling=False)
    
    return None


def get_bokeh_updates(key: str = None, sync_counter: int = 0) -> list:
    """
    Lê os valores do localStorage usando streamlit_js_eval com KEY FIXA por combo.
    Key fixa = o componente não precisa de um segundo rerun para avaliar o JS.
    O Streamlit cacheia o resultado de streamlit_js_eval por key; uma key que não muda
    entre reruns retorna o último valor avaliado imediatamente.

    Args:
        key: Chave do componente bokeh_editable
        sync_counter: Ignorado — mantido por compatibilidade de assinatura.

    Returns:
        Lista de 12 valores ou None
    """
    packet = get_bokeh_update_packet(key=key, sync_counter=sync_counter)
    if not packet:
        return None

    values = packet.get("values")
    if isinstance(values, list) and len(values) == 12:
        return values
    return None


def get_bokeh_update_packet(key: str = None, sync_counter: int = 0) -> dict:
    """
    Lê valores + timestamp do localStorage via streamlit_js_eval.
    A chave de avaliação varia por ciclo de sincronização para evitar cache estático
    e permitir capturar novas edições sucessivas.

    Args:
        key: Chave do componente bokeh_editable
        sync_counter: Ignorado — mantido por compatibilidade de assinatura.

    Returns:
        Dict {'values': list|None, 'timestamp': int, 'probe': dict|None, 'sync_probe': dict|None} ou None.
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
        print(
            "[get_bokeh_update_packet][RUNTIME] "
            f"python={sys.executable} "
            f"streamlit_js_eval_ok=True "
            f"key={key}"
        )

        storage_key = f"bokeh_update_{key or 'default'}"
        eval_key = f"_get_bokeh_packet_{key}_{int(sync_counter or 0)}"
        js_expr = (
            f"(function(){{"
            f"let store=localStorage;"
            f"try{{if(window.parent&&window.parent!==window&&window.parent.localStorage){{store=window.parent.localStorage;}}}}catch(_e){{store=localStorage;}}"
            f"const raw=store.getItem('{storage_key}');"
            f"const ts=store.getItem('{storage_key}_timestamp');"
            f"const probeRaw=store.getItem('{storage_key}_probe');"
            f"const syncProbeRaw=store.getItem('{storage_key}_sync_probe');"
            f"let values=null;"
            f"let probe=null;"
            f"let syncProbe=null;"
            f"try{{values=raw?JSON.parse(raw):null;}}catch(_e){{values=null;}}"
            f"try{{probe=probeRaw?JSON.parse(probeRaw):null;}}catch(_e){{probe=null;}}"
            f"try{{syncProbe=syncProbeRaw?JSON.parse(syncProbeRaw):null;}}catch(_e){{syncProbe=null;}}"
            f"return JSON.stringify({{values:values,timestamp:ts?Number(ts):0,probe:probe,sync_probe:syncProbe}});"
            f"}})()"
        )

        result = streamlit_js_eval(js_expressions=js_expr, key=eval_key)
        if not result:
            print(f"[get_bokeh_update_packet] sem_result key={eval_key}")
            return None

        packet = json.loads(result)
        if not isinstance(packet, dict):
            return None

        values = packet.get("values")
        timestamp = packet.get("timestamp", 0)
        probe = packet.get("probe") if isinstance(packet.get("probe"), dict) else None
        sync_probe = packet.get("sync_probe") if isinstance(packet.get("sync_probe"), dict) else None
        try:
            timestamp = int(timestamp or 0)
        except Exception:
            timestamp = 0

        if isinstance(values, list) and len(values) == 12:
            print(
                f"[get_bokeh_update_packet] ✓ Valores lidos (ts={timestamp}): "
                f"{[f'{v:.0f}' for v in values[:3]]}..."
            )
            return {
                "values": values,
                "timestamp": timestamp,
                "probe": probe,
                "sync_probe": sync_probe,
            }

        if timestamp > 0:
            return {
                "values": None,
                "timestamp": timestamp,
                "probe": probe,
                "sync_probe": sync_probe,
            }
    except Exception as e:
        print(
            "[get_bokeh_update_packet] Erro: "
            f"{e} | python={sys.executable} | spec={importlib.util.find_spec('streamlit_js_eval')}"
        )

    return None


def limpar_localStorage(key: str = None):
    """
    Limpa o localStorage do navegador para uma key específica ou todas as keys bokeh_update.
    Deve ser chamado quando quiser resetar os dados do drag-and-drop.
    
    Args:
        key: Chave específica para limpar. Se None, limpa todas as keys bokeh_update_*.
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
        import streamlit as st
        
        # Incrementa contador para garantir execução única
        clear_counter = st.session_state.get("_clear_counter", 0)
        st.session_state["_clear_counter"] = clear_counter + 1
        
        if key:
            storage_key = f"bokeh_update_{key}"
            js_code = f"localStorage.removeItem('{storage_key}')"
        else:
            # Limpa todas as keys que começam com bokeh_update_
            js_code = """
            (function() {
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    if (k && k.startsWith('bokeh_update_')) {
                        keysToRemove.push(k);
                    }
                }
                keysToRemove.forEach(k => localStorage.removeItem(k));
                return keysToRemove.length;
            })()
            """
        
        streamlit_js_eval(
            js_expressions=js_code,
            key=f"_clear_ls_{clear_counter}"
        )
        
    except Exception as e:
        print(f"[limpar_localStorage] Erro: {e}")


def salvar_localStorage(key: str, valores: list):
    """
    Salva valores diretamente no localStorage do navegador.
    Útil quando os valores são modificados via botões Streamlit.
    
    Args:
        key: Chave do componente bokeh_editable
        valores: Lista de 12 valores a serem salvos
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
        import streamlit as st
        
        if not valores or len(valores) != 12:
            return
        
        storage_key = f"bokeh_update_{key}"
        valores_json = json.dumps([float(v) for v in valores])
        
        # Incrementa contador para garantir execução única
        save_counter = st.session_state.get("_save_counter", 0)
        st.session_state["_save_counter"] = save_counter + 1
        
        js_code = f"""
        (function() {{
            localStorage.setItem('{storage_key}', '{valores_json}');
            localStorage.setItem('{storage_key}_timestamp', Date.now().toString());
            return true;
        }})()
        """
        
        streamlit_js_eval(
            js_expressions=js_code,
            key=f"_save_ls_{save_counter}"
        )
        
    except Exception as e:
        print(f"[salvar_localStorage] Erro: {e}")


def check_for_updates(key: str, current_values: list, threshold_ms: int = 2000) -> tuple:
    """
    Verifica se há atualizações recentes no localStorage.
    Usado para detectar quando o usuário arrastou pontos no gráfico.
    
    Args:
        key: Chave do componente bokeh_editable
        current_values: Valores atuais no session_state
        threshold_ms: Janela de tempo (ms) para considerar uma atualização como "recente"
    
    Returns:
        (needs_update, new_values): Tupla com flag e novos valores
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
        import streamlit as st
        import time
        
        storage_key = f"bokeh_update_{key}"
        
        # Contador único para essa verificação
        check_counter = st.session_state.get("_check_counter", 0)
        st.session_state["_check_counter"] = check_counter + 1
        
        # Lê valores e timestamp do localStorage
        js_code = f"""
        (function() {{
            const data = localStorage.getItem('{storage_key}');
            const ts = localStorage.getItem('{storage_key}_timestamp');
            return JSON.stringify({{data: data, timestamp: ts}});
        }})()
        """
        
        result = streamlit_js_eval(
            js_expressions=js_code,
            key=f"_check_ls_{check_counter}"
        )
        
        if result:
            parsed = json.loads(result)
            data_str = parsed.get('data')
            timestamp_str = parsed.get('timestamp')
            
            if data_str and timestamp_str:
                new_values = json.loads(data_str)
                timestamp = int(timestamp_str)
                now = int(time.time() * 1000)
                
                # Verifica se é recente e diferente dos valores atuais
                if now - timestamp < threshold_ms:
                    if isinstance(new_values, list) and len(new_values) == 12:
                        current_rounded = [round(v, 2) for v in (current_values or [])]
                        new_rounded = [round(v, 2) for v in new_values]
                        
                        if current_rounded != new_rounded:
                            return (True, new_values)
        
    except Exception as e:
        print(f"[check_for_updates] Erro: {e}")
    
    return (False, None)
