import pypdf
import re
import os

DESCRICAO = "(DIFAL)"
PADRAO_VALOR = r"R\$ ?(-?\d{1,3}(?:\.\d{3})*,\d{2})" 

def extrair_valores_por_mes(caminho_pdf):
    doc = pypdf.PdfReader(caminho_pdf)
    total = 0.0
    counter = 0
    for pagina in doc.pages:
        texto = pagina.extract_text()
        if not texto:
            continue

        linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]

        for linha in linhas:
            if DESCRICAO in linha:
                match = re.search(PADRAO_VALOR, linha)
                if match:
                    valor_str = match.group(1).replace(".", "").replace(",", ".")
                    valor_float = float(valor_str)
                    total += valor_float
                    print(f"total: {total:+.2f}")  # Exibe o sinal
                    counter += 1
                    print(f"{counter} Linha: {linha} | Valor extraído: R$ {valor_float:+.2f}")

    print(f"Numero de Valores: {counter}")
    return total, counter

# Pasta com os arquivos PDF
pasta = './'
arquivos_pdf = sorted([f for f in os.listdir(pasta) if f.lower().endswith('.pdf')])

totais_por_mes = {}

for arquivo in arquivos_pdf:
    caminho_completo = os.path.join(pasta, arquivo)
    nome_mes = os.path.splitext(arquivo)[0].lower()

    if os.path.exists(caminho_completo):
        total_mes, counter = extrair_valores_por_mes(caminho_completo)
        totais_por_mes[nome_mes] = [total_mes, counter]
        print(f"\nTotal em {nome_mes.capitalize()}: R$ {total_mes:+.2f}")
    else:
        print(f"Arquivo não encontrado: {caminho_completo}")

# Resultado final
print("\n--- Resumo por Mês ---")
for mes, total in totais_por_mes.items():
    print(f"{mes.capitalize()}: R$ {total[0]:+.2f} Qtde {total[1]}")  # Exibe o sinal

print("\nFim do processamento.")