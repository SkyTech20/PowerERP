# PowerERP — Demo de produtos de bordo: roteiro de testes

Roteiro para conferir o cenário de demonstração **Maple products** (o padrão do ERP): a Érablière Démo inc., uma usine de Saint-Georges (Beauce) que compra sirop d'érable em barris de três érablières e faz sirop em lata e em garrafa, beurre d'érable, bonbons e sucre à la crème. O demo já abre com outubro e novembro de 2026 feitos pelo próprio ERP: ordens de produção, passos das receitas, faturas postadas, uma nota de crédito, lotes retidos e não conformidades. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha **Maple products** e clique **Reset demo data**.

---

## 1. O cenário

| Passo | Esperado |
|---|---|
| **Administration > System settings**, lista *Data set* | *Maple products (syrup, butter, candy; production, sales, quality)* em primeiro, depois *SkyAI* e *Manufacturing*. O *Pastry shop* não existe mais. |
| Botão **FR** | A opção vira *Produits de l'érable (sirop, beurre, bonbons ; production, ventes, qualité)*. O **?** do card explica o demo. |
| **Dashboard** | 6 fornecedores, 8 pedidos de compra (1 aberto), 7 recepções, valor do estoque 11 966,96 $. |
| **Sales > Customers** | 4 clientes: EPICERIE-STDENIS, BOUTIQUE-VQ, LAURENTIAN-HOTELS (em inglês) e DISTRIB-CHAUDIERE (escompte de 3 %). |
| **Sales > Price lists** | RETAIL, DISTRIB (preço por palete a partir de 300 latas) e HOTELS. |
| Uma instalação que já tinha dados e nunca escolheu cenário | Depois da atualização, continua com os mesmos dados (o ERP não troca sozinho para o demo de bordo). |

## 2. Cadastros

| Passo | Esperado |
|---|---|
| **Inventory > Items** | 21 produtos. Acabados (*Finished product*): MAPLE-SYRUP-540, MAPLE-SYRUP-250, MAPLE-BUTTER-200, MAPLE-CANDY-12, MAPLE-FUDGE-250. Semi-acabado (*Kit/Assembly*): SYRUP-STD. Matérias-primas: SYRUP-BULK-AMB, SYRUP-BULK-DRK, CREAM-35, BUTTER e as embalagens. Ativos: CANDY-COOKER, FILLER. |
| Abrir MAPLE-SYRUP-540 | *Sales tax group* ZERO (sirop puro é alimento básico, isento). MAPLE-CANDY-12 e MAPLE-FUDGE-250: QC (TPS + TVQ). Lote e validade controlados, *Pick policy* FEFO. |
| Abrir SYRUP-BULK-AMB | Lote e validade controlados (730 dias). Três fornecedores na aba de compra: GAGNON (preferido), CANTONS e TREMBLAY. |
| **Inventory > Warehouses**, PLANT | Locais BAR-01 a BAR-12 (um barril por local), TANK-01/02, COLD-01 a 04, PACK-01, PROD-01 e FG-01 a 12. |
| **Production > Recipes**, MAPLE-BUTTER-200 A | Passos: *Cook to 112 °C* (111 a 113, crítico, segura o lote) e *Cool below 10 °C before whipping* (máximo 10, crítico, segura o lote). |
| MAPLE-FUDGE-250 A | Materiais SYRUP-STD, CREAM-35, BUTTER; passo crítico *Label shows the allergen "milk"* que bloqueia. |
| SYRUP-STD A | Passo crítico *Syrup Brix (66 to 68.9)* que bloqueia, e *Taste and smell of the barrels are right*. |

## 3. A história de outubro e novembro

| Passo | Esperado |
|---|---|
| **Production > Production orders** | 13 ordens: 10 *Closed*, a 9 (MAPLE-CANDY-12) *Completed*, a 12 *Released* (latas para 30/11) e a 13 *Draft*. |
| Abrir a ordem 9 | Card *Recipe steps*: *Cook to 115 °C* com 118,5 °C, desvio "Above the maximum", comentário "Sonde du cuiseur 2 décalée...". Lote MO9. Completada um dia depois do prazo. |
| **Sales > Invoices** | Faturas 1 a 9 *Posted*, a nota de crédito NC-1 (6 barquetas de sucre à la crème amassadas, sem volta ao estoque) e 2 rascunhos (DISTRIB-CHAUDIERE e LAURENTIAN-HOTELS). |
| Abrir a fatura 2 (BOUTIQUE-VQ) | O xarope sem imposto; bala e sucre à la crème com TPS e TVQ. |
| Rascunho de LAURENTIAN-HOTELS (48 caixas de bala), **Post** | Erro "Not enough released stock...": sobram só 22 caixas liberadas, o lote MO9 está retido. Nada muda. |
| Rascunho de DISTRIB-CHAUDIERE, **Check** | Tudo disponível; pode ser postado. |
| **Quality > Nonconformances** | 1: Reception, barril T-140 (lote 900106-3) com gosto de bourgeon, *Closed*, *Return to supplier*. 2: Customer, MAPLE-FUDGE-250 MO5, *Closed*, *Use as is*. 3: Production, MAPLE-CANDY-12 MO9, *Open*. |
| **Quality > Lot status** | MAPLE-CANDY-12 MO9 *On hold* ("Order 9, step 10/20 Cook to 115 °C: 118.5 °C"). O barril 900106-3 *Rejected* (saiu do estoque: devolvido à Sucrerie Tremblay). |
| **Inventory > Stock on hand**, SYRUP-BULK-AMB | O lote 900106-3 não aparece (movimento de saída de 30/10 "Retour au fournisseur"). |

## 4. Rastreabilidade até a érablière

| Passo | Esperado |
|---|---|
| **Production > Lots and traceability**, MAPLE-SYRUP-540, lote MO8 | *Origin*: feita pela ordem 8 com o sirop padronizado MO1 e MO7; cada um vem dos barris, até o fornecedor e o lote do fornecedor (ex.: GAGNON, "B-0412 / récolte 2026-03-24"). Aparecem GAGNON, CANTONS e TREMBLAY, nunca o barril T-140. |
| Card *Customers* | DISTRIB-CHAUDIERE (fatura 6), LAURENTIAN-HOTELS (8) e EPICERIE-STDENIS (9). |
| Card *Stock on hand* | MO8, 236 UN em FG-06. |
| SYRUP-BULK-AMB, lote 900102-1 | *Uses*: ordem 1 fez o SYRUP-STD MO1, que fez latas, beurre, balas e sucre à la crème: o recall alcança todos os clientes desses lotes. |

## 5. Indicadores SCOR

**Reports > Supply chain indicators** (últimos 90 dias até 26/11/2026)

| Cartão | Esperado |
|---|---|
| *Perfect orders* | 88,9 %, 8 de 9 faturas (a fatura 5 tem nota de crédito). |
| *Production on time* | 90,9 %, 10 de 11 ordens (a 9 atrasou). |
| *Production yield* | 99,7 % (796 latas de 800 e 388 caixas de bala de 400). |
| *Supplier fill rate* | 99,9 % (o barril T-118 veio com 266 kg de 280). |
| *Receptions without a problem* | 85,7 %, 6 de 7. |
| *Steps right first time* | 97,6 %, 41 de 42. |
| *Lots held back* | 681,20 $: MO9. |
| *Lots to expire* | A crème 900105-1 vencida em 27/10 e a 900107-1 e o beurre perto de vencer. |
| Card *Deviations on the shop floor* | A ordem 9, 118,5 °C, *the lot is held*. |

Todos os cartões têm valor. Com o passar dos dias, os 90 dias param de cobrir outubro: use *From* 2026-09-01.

## 6. Refazer o demo (desenvolvedor)

| Passo | Esperado |
|---|---|
| `pip install time-machine`; `MAPLE_DATABASE_URL=postgresql+psycopg://...powererp_scratch python tools/make_maple_data.py` | Regrava `data/maple/*.json` e `story.json`. Rodar duas vezes dá o mesmo resultado. Um banco cujo nome não tem "scratch" nem "test" é recusado (ele é apagado). |
