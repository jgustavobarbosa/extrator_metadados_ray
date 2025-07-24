import os
import json
import openai
from pathlib import Path
from getpass import getpass
from tqdm import tqdm
from openai import OpenAI

def main():
    # === CONFIGURAÇÃO DA API ===
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = getpass("Insira sua chave da OpenAI: ")
    
    if os.getenv("OPENAI_API_KEY"):
        print("✅ Chave carregada com sucesso.")
    else:
        print("❌ Chave não configurada.")
        return

    # === CONFIGURAÇÕES DO MODELO ===
    LLM_CONFIG = {
        'model': 'gpt-3.5-turbo-0125',
        'timeout': 60
    }

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # === FUNÇÃO DE EXTRAÇÃO COM JSON ===
    def extrair_metadados(texto):
        prompt_sistema = """Você é um assistente jurídico. Extraia os seguintes dados em formato JSON:
        {
            "numero_processo": str,
            "tribunal": str,
            "medicamento_principal": str,
            "outros_medicamentos": list,
            "valor_pedido": float,
            "tipo_tutela": str,
            "status_tutela": str,
            "polo_ativo": str,
            "polo_passivo": str,
            "juiz_responsavel": str,
            "tipo_decisao": str,
            "CID": str,
            "fundamentacao_resumida": str
        }
        Regras:
        1. Use 'Não consta' para campos ausentes
        2. Mantenha números como float (valor_pedido)
        3. Liste múltiplos medicamentos como array
        4. Retorne APENAS o JSON válido, sem comentários"""

        try:
            response = client.chat.completions.create(
                model=LLM_CONFIG['model'],
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Texto do processo:\n\n{texto[:15000]}"}  # Limite de caracteres
                ],
                temperature=0.1,
                max_tokens=1024
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"erro": str(e)}

    # === PROCESSAMENTO DE ARQUIVOS ===
    def processar_pasta_json(pasta_json):
        resultados = []
        arquivos = list(Path(pasta_json).glob("*.json")
        
        if not arquivos:
            print(f"❌ Nenhum arquivo JSON encontrado em {pasta_json}")
            return resultados

        for arquivo in tqdm(arquivos, desc="Processando arquivos"):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for entrada in dados:
                    for item in entrada.get("items", []):
                        texto = item.get("texto_original") or item.get("texto", "")
                        if texto.strip():
                            resultado = extrair_metadados(texto)
                            resultados.append({
                                "arquivo_origem": arquivo.name,
                                "numero_processo": item.get("numero_processo_com_mascara"),
                                "tribunal": item.get("sigla_tribunal"),
                                "resultado_llm": resultado
                            })
            except Exception as e:
                print(f"⛔ Erro em {arquivo.name}: {str(e)}")
        return resultados

    # === SALVAR RESULTADOS ===
    def salvar_resultados(resultados, saida_path):
        with open(saida_path, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print(f"\n💾 {len(resultados)} registros salvos em {saida_path}")

    # === EXECUÇÃO ===
    pasta = input("📂 Caminho da pasta com JSONs: ").strip()
    saida = input("💾 Nome do arquivo de saída (ex: resultados.json): ").strip()

    if not saida.endswith('.json'):
        saida += '.json'

    resultados = processar_pasta_json(pasta)
    
    if resultados:
        salvar_resultados(resultados, saida)
    else:
        print("❌ Nenhum dado processado. Verifique os arquivos de entrada.")

if __name__ == "__main__":
    main()