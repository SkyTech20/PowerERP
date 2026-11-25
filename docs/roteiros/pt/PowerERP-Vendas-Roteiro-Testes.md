# PowerERP — Vendas: roteiro de testes (V1 a V6)

Roteiro para testar o módulo de vendas B2B (Quebec, CAD) no demo. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Manufacturing** logo depois de restaurar o demo.

**Antes de começar:** entre como administrador e vá em **Administration > System settings**. Escolha o cenário **Manufacturing** e restaure os dados de demo. Restaurar de novo volta tudo ao estado inicial, então dá para repetir o roteiro quantas vezes quiser.

---

## 1. Dados da empresa (V1)

**Administration > System settings > Company profile**

| Passo | Esperado |
|---|---|
| Abrir o card *Company profile* | Mostra Industries Démo PowerERP inc., endereço em Montréal e NEQ 1170000001. |
| Ver *GST / HST and QST numbers* | TPS 123456789 RT0001 e TVQ 1234567890 TQ0001. Esses números vêm dos códigos de imposto (**Administration > Taxes**) e não são digitados aqui. |
| *Invoice numbers start at* | Vazio ou 0, então a primeira invoice será a 1. Se você colocar 1001 e salvar, a próxima invoice postada recebe o número 1001. |

## 2. Clientes (V1)

**Sales > Customers**

| Cliente | O que conferir |
|---|---|
| HOTEL-LAURIER | Idioma FR, grupo de imposto QC, termos n30 (*net 30 jours*), tabela de preço HORECA. Tem dois endereços de entrega: HOTEL (padrão, Gatineau, QC) e OTTAWA (grupo ON). |
| MAPLE-FOODS | Idioma EN, Ontário, termos n45, tabela DIST. |
| CPE-SOLEIL | Creche isenta: grupo EXO, com número de isenção. |

Tente apagar o cliente HOTEL-LAURIER. O sistema recusa, porque o cliente está em uma invoice.

## 3. Tabelas de preço e conferência de preço (V2)

**Sales > Price lists** e a aba **Price check** do cliente.

| Passo | Esperado |
|---|---|
| HOTEL-LAURIER > *Price check*: TUBE-T8, qty 1 | Price 15.75 (HORECA), discount 3 % (desconto do cliente), net 15.2775. |
| Mesma consulta com qty 60 | Price 13.95, porque a HORECA tem quebra de quantidade a partir de 50. |
| MAPLE-FOODS: DOCK-USBC | Price 249.00, discount 4 %, net 239.04. |

## 4. Invoice em rascunho (V3)

**Sales > Invoices.** O demo já traz 3 rascunhos:

| Rascunho | Cliente | Impostos | Total |
|---|---|---|---|
| #1 | HOTEL-LAURIER (QC) | TPS 24.84 + TVQ 49.55 sobre 496.79 | **571.18** |
| #2 | MAPLE-FOODS (entrega em Toronto) | TVH-ON 13 % = 110.70 sobre 851.52 | **962.22** |
| #3 | CPE-SOLEIL (isenta) | nenhum | **170.57** |

**Conferir no rascunho #1:**
- Linhas: TUBE-T8 com 12 × 15.2775 = 183.33; CLAV-SF com 2 × 76.63 = 153.26; EXT-5LB com 2 × 80.10 = 160.20.
- *Discounts given*: 28.21.

**Criar uma invoice nova (botão New):**
1. Escolha o cliente HOTEL-LAURIER. O sistema propõe a entrega HOTEL, o depósito ENT-01, o idioma French e os termos n30.
2. Clique em *Add line*, escolha TUBE-T8 e digite qty 10. Preço, desconto, impostos e totais aparecem enquanto você digita: amount 152.78, TPS 7.64, TVQ 15.24, total 175.66.
3. Troque *Ship to* para OTTAWA. Os impostos passam a ser TVH-ON 13 %, porque o imposto segue o local de entrega.
4. Adicione PAIN-BL-675 (pão). A linha fica com grupo ZERO, sem imposto, e os outros produtos continuam tributados.
5. Digite um preço à mão (por exemplo 16) e salve. O preço é mantido.
6. Para testar o preço mínimo, coloque um *Min price* no produto acima do preço líquido. Ao salvar a invoice, aparece o erro de preço abaixo do mínimo.

## 5. Postar a invoice (V4)

**Ordem de baixa por produto:** em **Inventory > Products >** produto **> aba Inventory**, o campo *Stock out order* tem estas opções:
- *Automatic*: FEFO se o produto tem validade, senão FIFO.
- *FEFO*: sai primeiro o que vence antes.
- *FIFO*: sai primeiro o que entrou primeiro.
- *LIFO*: sai primeiro o que entrou por último.

**Lote vencido nunca é vendido.**

| Passo | Esperado |
|---|---|
| Rascunho #1 > **Check** | *Ready to post*. *Stock to take out*: TUBE-T8 12 de B-01-02-A, CLAV-SF 2 de A-01-02-A, EXT-5LB 2 do lote L2026-09 (validade 2032-09-30). Nada é alterado. |
| Mude TUBE-T8 para 500 e clique **Check** | *To fix before posting*: estoque insuficiente na linha 1 (500 UN > 100 UN). **Post** recusa e nada sai do estoque. |
| Volte para 12, clique **Post** e confirme | A invoice recebe o número **1** (ou o número inicial configurado) e fica *Posted*, só leitura. *Cost of goods sold* = 418.88. *Stock taken out* mostra o custo por linha. |
| **Inventory > Stock movements** | 3 saídas OUT, documento SO 1. |
| **Inventory > Stock** | TUBE-T8 em B-01-02-A caiu de 100 para 88. |
| Na invoice postada | Não há Save nem Delete. A API responde 409 se alguém tentar alterar ou apagar. |

**Teste de FEFO, FIFO e LIFO com EXT-5LB:**
1. Faça uma entrada manual (**Inventory > Stock movements**, tipo IN) de 2 unidades do lote L2027-03, validade 2031-03-31, em B-01-02-A.
2. Crie uma invoice com 3 EXT-5LB e clique **Check**.
   - *Automatic* (= FEFO): sai L2027-03 × 2 e depois L2026-09 × 1.
   - FIFO: sai L2026-09 × 3, que entrou primeiro.
   - LIFO: sai L2027-03 × 2 e L2026-09 × 1, porque L2027-03 entrou por último.

## 6. Impressão FR/EN (V5)

Botão **Print** na invoice. Abre a página para imprimir ou salvar em PDF pelo navegador.

| Passo | Esperado |
|---|---|
| Invoice 1 postada | Em francês: FACTURE, n° 1, empresa com TPS/TVQ e NEQ, *Facturer à* e *Livrer à*, *Échéance* = data + 30 dias, PO do cliente, linhas com o lote do extintor, impostos com o número de registro, total em CAD e a nota da empresa. |
| Rascunho #2 (MAPLE-FOODS) | Em inglês: INVOICE — DRAFT, marca d'água DRAFT, *Draft no.* 2, TVH-ON, vencimento em 45 dias. |
| Forçar idioma | Acrescente `?lang=en` (ou `fr`) no endereço da página de impressão. |

## 7. Nota de crédito (V6)

| Passo | Esperado |
|---|---|
| Na invoice 1 postada, clique **Credit note** e confirme | Abre uma nota de crédito em rascunho com todas as linhas da invoice. Cliente, entrega, idioma e impostos vêm da invoice e não podem ser alterados. *Invoice credited* = 1. Cada linha tem *Return* marcado. |
| Deixe só a linha TUBE-T8 com qty 2 (apague as outras) | Subtotal 30.56, impostos 4.58, total 35.14, no preço e desconto da invoice. |
| Tente qty 13 em TUBE-T8 | Erro: mais que a quantidade faturada e ainda não creditada. |
| **Check** e depois **Post** | Número **NC-1**. *Stock brought back*: 2 UN em B-01-02-A, ao custo de saída (25.48). Em **Stock movements** aparece um ajuste ADJ +2, documento SO NC-1. |
| Desmarque *Return* em uma linha | A linha só credita o preço (ajuste de preço) e nada volta ao estoque. |
| **Credit note** de novo na invoice 1 | Traz só o que falta creditar (TUBE-T8 10, CLAV-SF 2, EXT-5LB 2). Com tudo creditado: *Every line of this invoice is already credited*. |
| Lotes e séries | Uma linha com lote volta para o mesmo lote e validade. Um notebook com número de série (LAP-14I7) volta com a mesma série. |
| **Print** na nota postada | NOTE DE CRÉDIT, n° NC-1, *Facture créditée* 1. |
| Lista **Sales > Invoices** | Coluna *Type* (Invoice / Credit note) e filtro por tipo. |

## 8. Cenário Pastry shop

Em **Administration > System settings**, mude para **Pastry shop**. O demo traz:
- 3 rascunhos: Café du Plateau, Traiteur Royal e Ottawa Deli (este com TVH-ON).
- Estoque inicial de pastéis prontos (lote de 18/11 no local SHOP-01 e lote de 19/11 no SHOP-02, um lote por produto em cada local), para que os rascunhos possam ser postados.

Os pastéis usam FIFO (não têm validade). Ao postar o rascunho de Café du Plateau, saem primeiro os lotes de 18/11.

---

## Referência rápida da API

| Ação | Chamada |
|---|---|
| Listar e criar | `GET/POST /api/sales-invoices` |
| Ler, alterar e apagar um rascunho | `GET/PUT/DELETE /api/sales-invoices/<no>` |
| Calcular sem salvar | `POST /api/sales-invoices/calc`, `/<no>/calc` |
| Verificar e postar | `POST /api/sales-invoices/<no>/check`, `/<no>/post` |
| Nota de crédito a partir da invoice | `POST /api/sales-invoices/<no>/credit` |
| Imprimir | `GET /api/sales-invoices/<no>/print?lang=fr\|en` |
| Conferir preço | `GET /api/pricing?customer=&product=&qty=&uom=&date=` |
