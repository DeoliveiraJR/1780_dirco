"""
Componente Streamlit para Bokeh com comunicação bidirecional.
Usa components.html() + localStorage + streamlit_js_eval para capturar eventos.
"""
import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
from bokeh.resources import CDN
import json


def bokeh_editable(
    bokeh_figure,
    height: int = 1200,
    key: str = None
) -> list:
    """
    Renderiza um gráfico Bokeh com monitoramento de mudanças nos DataSources.
    Quando o usuário arrasta pontos, os novos valores são salvos no localStorage
    e podem ser lidos pelo Python via get_bokeh_updates().
    
    Args:
        bokeh_figure: O objeto Bokeh (figure ou layout) a ser renderizado
        height: Altura do componente em pixels
        key: Chave única do Streamlit para este componente
    
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
            
            allModels.forEach((model, id) => {
                if (model.type === 'ColumnDataSource') {
                    if (model.data && model.data.y && model.data.y.length === 12) {
                        console.log('[BokehEditable] Monitorando:', model.name || model.id);
                        
                        model.connect(model.properties.data.change, () => {
                            const data = model.data;
                            if (data && data.y && data.y.length === 12) {
                                const yValues = Array.from(data.y).map(v => 
                                    Number.isFinite(v) ? parseFloat(v.toFixed(2)) : 0
                                );
                                
                                if (debounceTimer) clearTimeout(debounceTimer);
                                debounceTimer = setTimeout(() => saveToStorage(yValues), 300);
                            }
                        });
                    }
                }
            });
            
            console.log('[BokehEditable] Pronto!');
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
    Lê os valores atualizados do localStorage usando streamlit_js_eval.
    Retorna None se não houver atualizações.
    
    Args:
        key: Chave do componente bokeh_editable
        sync_counter: Contador de sincronização (incrementar para forçar nova leitura)
    
    Returns:
        Lista de 12 valores ou None
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
        
        storage_key = f"bokeh_update_{key or 'default'}"
        
        # Usa o sync_counter na key para forçar nova leitura quando necessário
        eval_key = f"_get_bokeh_{key}_{sync_counter}"
        
        # Lê o valor do localStorage
        result = streamlit_js_eval(
            js_expressions=f"localStorage.getItem('{storage_key}')",
            key=eval_key
        )
        
        if result:
            values = json.loads(result)
            if isinstance(values, list) and len(values) == 12:
                return values
    except Exception as e:
        print(f"[get_bokeh_updates] Erro: {e}")
    
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
