"""RentSmart - Orçamento de locação da R.M Imóveis.

Recebe as características da locação, aplica as regras comerciais,
mostra o orçamento detalhado e gera a projeção de 12 meses em CSV.
"""
import csv
from abc import ABC, abstractmethod

TAXA_CONTRATUAL = 2000.00
MAX_PARCELAS = 5
MESES_PROJECAO = 12


def moeda(valor):
    """Formata um número como moeda brasileira: R$ 1.234,56."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


# ----------------------------------------------------------------- imóveis
class Imovel(ABC):
    """Classe base: define o que todo imóvel precisa informar ao orçamento."""
    NOME = ""
    ALUGUEL_BASE = 0.0

    @abstractmethod
    def adicionais(self):
        """Retorna lista de (descrição, valor) dos adicionais aplicáveis."""

    def desconto(self, subtotal):
        """Retorna (descrição, valor) do desconto; padrão: nenhum."""
        return None

    @abstractmethod
    def descricao(self):
        """Texto curto com as escolhas do cliente."""


class Apartamento(Imovel):
    NOME = "Apartamento"
    ALUGUEL_BASE = 700.00
    ADICIONAL_2_QUARTOS = 200.00
    GARAGEM = 300.00
    DESCONTO_SEM_CRIANCAS = 0.05

    def __init__(self, quartos, garagem, tem_criancas):
        self.quartos = quartos
        self.garagem = garagem
        self.tem_criancas = tem_criancas

    def adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(("Segundo quarto", self.ADICIONAL_2_QUARTOS))
        if self.garagem:
            itens.append(("Vaga de garagem", self.GARAGEM))
        return itens

    def desconto(self, subtotal):
        if not self.tem_criancas:
            return ("Desconto 5% (sem crianças)", subtotal * self.DESCONTO_SEM_CRIANCAS)
        return None

    def descricao(self):
        return (f"Apartamento de {self.quartos} quarto(s), "
                f"{'com' if self.garagem else 'sem'} garagem, "
                f"{'com' if self.tem_criancas else 'sem'} crianças")


class Casa(Imovel):
    NOME = "Casa"
    ALUGUEL_BASE = 900.00
    ADICIONAL_2_QUARTOS = 250.00
    GARAGEM = 300.00

    def __init__(self, quartos, garagem):
        self.quartos = quartos
        self.garagem = garagem

    def adicionais(self):
        itens = []
        if self.quartos == 2:
            itens.append(("Segundo quarto", self.ADICIONAL_2_QUARTOS))
        if self.garagem:
            itens.append(("Vaga de garagem", self.GARAGEM))
        return itens

    def descricao(self):
        return (f"Casa de {self.quartos} quarto(s), "
                f"{'com' if self.garagem else 'sem'} garagem")


class Estudio(Imovel):
    NOME = "Estúdio"
    ALUGUEL_BASE = 1200.00
    PACOTE_INICIAL = 250.00      # 2 vagas
    VAGAS_NO_PACOTE = 2
    VAGA_EXTRA = 60.00

    def __init__(self, vagas):
        self.vagas = vagas       # 0 = não contratou estacionamento

    def adicionais(self):
        if self.vagas == 0:
            return []
        itens = [(f"Pacote de {self.VAGAS_NO_PACOTE} vagas", self.PACOTE_INICIAL)]
        extras = max(0, self.vagas - self.VAGAS_NO_PACOTE)
        if extras:
            itens.append((f"{extras} vaga(s) extra(s) x {moeda(self.VAGA_EXTRA)}",
                          extras * self.VAGA_EXTRA))
        return itens

    def descricao(self):
        return f"Estúdio com {self.vagas} vaga(s) de estacionamento"


# --------------------------------------------------------------- orçamento
class Orcamento:
    """Calcula o valor mensal, a taxa contratual e a projeção de 12 meses."""

    def __init__(self, imovel, parcelas_taxa):
        self.imovel = imovel
        self.parcelas_taxa = parcelas_taxa
        self.itens_adicionais = imovel.adicionais()
        self.subtotal = imovel.ALUGUEL_BASE + sum(v for _, v in self.itens_adicionais)
        self.desconto = imovel.desconto(self.subtotal)
        valor_desconto = self.desconto[1] if self.desconto else 0.0
        self.aluguel_mensal = round(self.subtotal - valor_desconto, 2)

    def parcelas_da_taxa(self):
        """Divide a taxa em parcelas; a última absorve a diferença de centavos."""
        n = self.parcelas_taxa
        valor = round(TAXA_CONTRATUAL / n, 2)
        parcelas = [valor] * n
        parcelas[-1] = round(TAXA_CONTRATUAL - valor * (n - 1), 2)
        return parcelas

    def resumo(self):
        linhas = ["=" * 52, "          ORÇAMENTO - R.M IMÓVEIS", "=" * 52,
                  self.imovel.descricao(), "-" * 52,
                  f"{'Aluguel-base':<34}{moeda(self.imovel.ALUGUEL_BASE):>18}"]
        for nome, valor in self.itens_adicionais:
            linhas.append(f"{'+ ' + nome:<34}{moeda(valor):>18}")
        linhas.append(f"{'Subtotal':<34}{moeda(self.subtotal):>18}")
        if self.desconto:
            linhas.append(f"{'- ' + self.desconto[0]:<34}{moeda(self.desconto[1]):>18}")
        linhas += [f"{'ALUGUEL MENSAL':<34}{moeda(self.aluguel_mensal):>18}", "-" * 52,
                   "Taxa contratual (cobrada à parte do aluguel)",
                   f"{'Valor da taxa':<34}{moeda(TAXA_CONTRATUAL):>18}",
                   f"{'Parcelamento':<34}"
                   f"{str(self.parcelas_taxa) + 'x de ' + moeda(self.parcelas_da_taxa()[0]):>18}",
                   "=" * 52]
        return "\n".join(linhas)

    def projecao(self):
        """Lista de 12 linhas: (mês, aluguel, parcela da taxa, total do mês)."""
        parcelas = self.parcelas_da_taxa()
        linhas = []
        for mes in range(1, MESES_PROJECAO + 1):
            taxa = parcelas[mes - 1] if mes <= len(parcelas) else 0.0
            linhas.append((mes, self.aluguel_mensal, taxa, round(self.aluguel_mensal + taxa, 2)))
        return linhas

    def exportar_csv(self, caminho="projecao_12_meses.csv"):
        """Gera o CSV (separador ';' e vírgula decimal, para abrir direto no Excel BR)."""
        fmt = lambda v: f"{v:.2f}".replace(".", ",")
        linhas = self.projecao()
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Mês", "Aluguel mensal", "Parcela da taxa contratual", "Total do mês"])
            for mes, aluguel, taxa, total in linhas:
                w.writerow([mes, fmt(aluguel), fmt(taxa), fmt(total)])
            w.writerow(["TOTAL 12 MESES",
                        fmt(sum(l[1] for l in linhas)),
                        fmt(sum(l[2] for l in linhas)),
                        fmt(sum(l[3] for l in linhas))])
        return caminho


# ------------------------------------------------- interface (terminal) ---
def ler_inteiro(pergunta, minimo, maximo):
    while True:
        texto = input(pergunta).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        print(f"  Entrada inválida. Digite um número de {minimo} a {maximo}.")


def ler_sim_nao(pergunta):
    while True:
        texto = input(pergunta + " (s/n): ").strip().lower()
        if texto in ("s", "sim"):
            return True
        if texto in ("n", "nao", "não"):
            return False
        print("  Entrada inválida. Digite 's' ou 'n'.")


def montar_imovel():
    print("\nTipo de imóvel:\n  1) Apartamento\n  2) Casa\n  3) Estúdio")
    tipo = ler_inteiro("Escolha: ", 1, 3)
    if tipo == 1:
        quartos = ler_inteiro("Quartos (1 ou 2): ", 1, 2)
        garagem = ler_sim_nao("Deseja vaga de garagem?")
        criancas = ler_sim_nao("Possui crianças?")
        return Apartamento(quartos, garagem, criancas)
    if tipo == 2:
        quartos = ler_inteiro("Quartos (1 ou 2): ", 1, 2)
        garagem = ler_sim_nao("Deseja vaga de garagem?")
        return Casa(quartos, garagem)
    vagas = ler_inteiro("Vagas de estacionamento (0 a 10; pacote inicial = 2 vagas): ", 0, 10)
    return Estudio(vagas)


def main():
    print("RentSmart - R.M Imóveis")
    imovel = montar_imovel()
    parcelas = ler_inteiro(f"Parcelas da taxa contratual (1 a {MAX_PARCELAS}): ", 1, MAX_PARCELAS)
    orcamento = Orcamento(imovel, parcelas)
    print("\n" + orcamento.resumo())
    print(f"\nArquivo gerado: {orcamento.exportar_csv()}")


if __name__ == "__main__":
    main()