"""Shared in-memory ZIP builder for CVM client tests — column names below
are taken from the real CVM files (confirmed live before implementing, not
guessed), trimmed to the minimum needed to exercise the parsing logic."""
import io
import zipfile

DRE_FIELDS = [
    "CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "GRUPO_DFP", "MOEDA",
    "ESCALA_MOEDA", "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC", "CD_CONTA", "DS_CONTA",
    "VL_CONTA", "ST_CONTA_FIXA",
]
BALANCE_FIELDS = DRE_FIELDS  # BPA_con/BPP_con share the same shape as DRE_con
DFC_FIELDS = DRE_FIELDS
DMPL_FIELDS = [
    "CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "GRUPO_DFP", "MOEDA",
    "ESCALA_MOEDA", "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC", "COLUNA_DF", "CD_CONTA",
    "DS_CONTA", "VL_CONTA", "ST_CONTA_FIXA",
]

FII_COMPLEMENTO_FIELDS = [
    "CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Total_Numero_Cotistas",
    "Patrimonio_Liquido", "Valor_Patrimonial_Cotas", "Percentual_Rentabilidade_Efetiva_Mes",
    "Percentual_Dividend_Yield_Mes",
]
FII_IMOVEL_FIELDS = [
    "CNPJ_Fundo_Classe", "Data_Referencia", "Versao", "Nome_Imovel", "Endereco", "Area",
    "Percentual_Vacancia", "Percentual_Inadimplencia", "Percentual_Receitas_FII",
    "Percentual_Locado",
]


def _csv_line(fields: list[str], values: dict) -> str:
    return ";".join(str(values.get(f, "")) for f in fields)


def dre_row(cvm_code="004170", versao="1", ordem="ÚLTIMO", cd_conta="3.01", ds_conta="", vl_conta="0", escala="MIL", dt_refer="2025-12-31"):
    return {
        "CNPJ_CIA": "1", "DT_REFER": dt_refer, "VERSAO": versao, "DENOM_CIA": "TEST S.A.",
        "CD_CVM": cvm_code, "GRUPO_DFP": "DF Consolidado", "MOEDA": "REAL",
        "ESCALA_MOEDA": escala, "ORDEM_EXERC": ordem, "DT_INI_EXERC": "2025-01-01",
        "DT_FIM_EXERC": dt_refer, "CD_CONTA": cd_conta, "DS_CONTA": ds_conta,
        "VL_CONTA": vl_conta, "ST_CONTA_FIXA": "S",
    }


def dmpl_row(cvm_code="004170", versao="1", coluna_df="Patrimônio Líquido Consolidado", cd_conta="5.04.06", ds_conta="Dividendos", vl_conta="0", escala="MIL", dt_refer="2025-12-31"):
    return {
        "CNPJ_CIA": "1", "DT_REFER": dt_refer, "VERSAO": versao, "DENOM_CIA": "TEST S.A.",
        "CD_CVM": cvm_code, "GRUPO_DFP": "DF Consolidado", "MOEDA": "REAL",
        "ESCALA_MOEDA": escala, "ORDEM_EXERC": "ÚLTIMO", "DT_INI_EXERC": "2025-01-01",
        "DT_FIM_EXERC": dt_refer, "COLUNA_DF": coluna_df, "CD_CONTA": cd_conta,
        "DS_CONTA": ds_conta, "VL_CONTA": vl_conta, "ST_CONTA_FIXA": "S",
    }


def build_zip(files: dict[str, list[dict]], fields_by_file: dict[str, list[str]]) -> bytes:
    """`files`: {filename: [row_dict, ...]}. `fields_by_file`: {filename: [column names]}."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for filename, rows in files.items():
            fields = fields_by_file[filename]
            lines = [";".join(fields)] + [_csv_line(fields, row) for row in rows]
            content = "\n".join(lines).encode("latin1")
            zf.writestr(filename, content)
    return buffer.getvalue()
