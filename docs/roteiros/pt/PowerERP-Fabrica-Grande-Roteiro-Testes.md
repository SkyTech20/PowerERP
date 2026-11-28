# PowerERP — Fábrica do zero com três depósitos: roteiro de testes

Roteiro para testar o ERP inteiro **começando do zero**, como um cliente novo: configuração da empresa (com logo), plano de contas e centros de custo, impostos, unidades, três depósitos com rua, prateleira e andar, fornecedores, produtos, receitas, compras, recepções, produção em duas etapas, qualidade, vendas, nota de crédito e rastreabilidade até o fornecedor.

A fábrica é a **Les Aliments Nordiques inc.**, de Lévis (QC). Ela compra fraises congeladas, açúcar, pectina e embalagens, cozinha uma **purée de fraises** (produto intermediário) e com ela faz **dois produtos finais**: confiture de fraises em pote de 250 ml e pâtes de fruits em sachet de 200 g.

| Depósito | Para quê | Locations (zona-rua-prateleira-andar) |
|---|---|---|
| **MP** | Matéria-prima e embalagens | R-A-01-1 a R-B-03-3 (2 ruas × 3 prateleiras × 3 andares = 18) + QUAI (recepção) |
| **INT** | Intermediário (purée) | T-A-01 a T-A-04 (4 tanques) |
| **PF** | Produtos finais | F-A-01-1 a F-B-04-2 (2 ruas × 4 prateleiras × 2 andares = 16) + EXPED (expedição) |

Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados foram conferidos no ERP em 2026-11-28. Use as datas indicadas (1 a 3 de dezembro de 2026) para ter os mesmos vencimentos.

**Antes de começar:** entre como administrador. Tenha à mão uma imagem do logo (PNG, JPEG, GIF ou WEBP, até 5 MB).

---

## 0. Começar do zero

| Passo | Esperado |
|---|---|
| **Administration > System settings**, card *Data*, **Clear all data** e confirmar | Mensagem "All data cleared." Usuários, perfis e configurações continuam. |
| **Inventory > Products**, **Suppliers**, **GL Accounts / Cost Centers** | Listas vazias. |

> Os números das ordens de produção, das não conformidades e das notas de crédito continuam de onde estavam (não se repetem nunca, nem depois de limpar). Anote o número que o ERP der e use-o nos passos seguintes. As faturas recomeçam no número definido na empresa.

## 1. A empresa e o logo

**Administration > System settings**, card *Company*

| Campo | Valor |
|---|---|
| *Name* | Aliments Nordiques |
| *Legal name* | Les Aliments Nordiques inc. |
| Endereço | 2400, boulevard de la Rive-Sud, Lévis, QC, G6W 6N9, CA |
| *Phone* / *E-mail* / *Website* | 418 555-0700 / factures@aliments-nordiques.ca / www.aliments-nordiques.ca |
| *Quebec enterprise number (NEQ)* | 1170000099 |
| *Invoice numbers start at* | 5001 |
| *Invoice note (French)* | Merci de votre confiance ! Paiement par virement : voir les coordonnées au verso. |
| *Invoice note (English)* | Thank you for your business! Payment by bank transfer: see the details overleaf. |

| Passo | Esperado |
|---|---|
| **Save** | "Company profile saved." |
| *Logo*: aparece "No logo". **Choose an image…** e escolher um arquivo .pdf ou .txt | Recusado: "This file is not an image the ERP can read (use PNG, JPEG, GIF or WebP)." |
| Escolher uma imagem de mais de 5 MB | Recusado: "The image is too big (5 MB at most)." |
| Escolher o logo certo | "Logo saved." A prévia aparece; o botão vira **Change the logo…** e surge **Remove the logo**. Uma imagem grande é reduzida (cabe em 600 × 240) e girada conforme a foto. |
| Recarregar a página (F5) | O logo continua. |
| **Remove the logo**, confirmar, e depois escolher de novo | Some ("No logo") e volta. Deixe o logo para o resto do roteiro. |
| Ícone **?** do card | A ajuda explica onde o logo é impresso (faturas, notas de crédito e Excel de rastreabilidade). |

## 2. Plano de contas (GL accounts)

**General Ledger > GL Accounts / Cost Centers**, aba *GL accounts*, **New** para cada conta. Deixe *Type* em branco: o ERP sugere pelo primeiro dígito.

| Account | Description (French) | Description (English) | Requires a cost center |
|---|---|---|---|
| 1100 | Banque | Bank | |
| 1310 | Stock - matières premières | Inventory - raw materials | |
| 1320 | Stock - produits semi-finis | Inventory - semi-finished goods | |
| 1330 | Stock - produits finis | Inventory - finished goods | |
| 2100 | Comptes fournisseurs | Accounts payable | |
| 2310 | TPS à recevoir | GST receivable | |
| 2320 | TVQ à recevoir | QST receivable | |
| 2330 | TPS à payer | GST payable | |
| 2340 | TVQ à payer | QST payable | |
| 4100 | Ventes - confitures | Sales - jams | |
| 4200 | Ventes - confiseries | Sales - confectionery | |
| 5100 | Achats - matières premières | Purchases - raw materials | |
| 5110 | Achats - emballages | Purchases - packaging | |
| 5200 | Coût des produits vendus | Cost of goods sold | |
| 5700 | Entretien et réparations | Maintenance and repairs | ✔ |

| Passo | Esperado |
|---|---|
| Lista | 15 contas com o tipo em cor: 1xxx *Asset*, 2xxx *Liability*, 4xxx *Revenue*, 5xxx *Expense*. Filtros *Type* e *Active*. |
| Botão **EN**/**FR** | A descrição troca de idioma. |
| Abrir 5700 | *Requires a cost center* marcado. |
| Criar 1100 de novo | Recusado: código já existe. |

## 3. Centros de custo (departamento e subdepartamento)

O GL account e o centro de custo são **independentes**: um não fica dentro do outro. Eles só se encontram na linha de uma compra (fatura de fornecedor ou recepção): a conta diz **o quê** (ex.: 5700 manutenção), o centro de custo diz **quem** gastou (ex.: 200-210 cozinha).

Aba *Cost centers*:

| Department (CC1) | Sub-department (CC2) | Description (French) | Description (English) |
|---|---|---|---|
| 100 | | Administration | Administration |
| 200 | | Production | Production |
| 200 | 210 | Cuisson (purée) | Cooking (puree) |
| 200 | 220 | Remplissage et emballage | Filling and packing |
| 300 | | Entrepôts | Warehouses |
| 400 | | Ventes | Sales |
| 500 | | Qualité | Quality |

| Passo | Esperado |
|---|---|
| Para 210 e 220: abrir o 200 e usar **＋ Sub-department** | Formulário novo já com *Department* 200. |
| Lista | Em árvore: 200 Production e, abaixo, ↳ 210 e ↳ 220. |
| Criar 600 / 610 (subdepartamento sem o departamento) | "Create the department (CC1 alone) first, then its sub-departments." |
| Apagar o 200 | Recusado: ele tem subdepartamentos. |

## 4. Impostos

**Administration > Taxes**

| Passo | Valor / esperado |
|---|---|
| *Tax code* TPS | *Kind* GST, jurisdição CA, número 701234567 RT0001, GL cobrado 2330, GL recuperável 2310, 100 % recuperável, taxa 5 % desde 2008-01-01. |
| *Tax code* TVQ | *Kind* PST, jurisdição QC, número 1201234567 TQ0001, GL 2340 / 2320, taxa 9,975 % desde 2013-01-01. |
| *Tax group* QC | Québec - TPS + TVQ, *Treatment* Taxable, linhas TPS e TVQ (sem imposto sobre imposto). |
| *Tax group* ZERO | Détaxé (aliments de base), *Treatment* Zero-rated, sem linhas. |
| Calcular 100,00 $ no grupo QC | TPS 5,00 + TVQ 9,98 = 114,98 $. |
| **Administration > System settings**, *Tax registration numbers* | Aparecem os números da TPS e da TVQ (saem na fatura). |

## 5. Unidades e categorias

**Inventory > Categories / units**

| Passo | Valor |
|---|---|
| Unidades | KG (Kilogramme / Kilogram, peso), G (Gramme / Gram, peso), UN (Unité / Each, contagem). |
| Conversão | 1 KG = 1000 G. |
| Categorias | RAW Matières premières / Raw materials; PACK Emballages / Packaging; WIP Produits semi-finis / Semi-finished products; FG Produits finis / Finished products. |

## 6. Depósitos e locations (rua, prateleira, andar)

**Inventory > Warehouses / locations**, **New** para cada depósito (endereço da fábrica, *Type* Main, *Uses locations* marcado):

| Code | Name (French) | Name (English) |
|---|---|---|
| MP | Entrepôt des matières premières | Raw materials warehouse |
| INT | Entrepôt des produits semi-finis | Semi-finished goods warehouse |
| PF | Entrepôt des produits finis | Finished goods warehouse |

| Passo | Esperado |
|---|---|
| Abrir MP | Duas abas: *General* e *Locations*. A aba *Locations* diz "No location yet…". |
| Aba *Locations*, card *Generate locations*: *Zone* R, *Aisle* A até B, *Rack* 01 até 03, *Level* 1 até 3, *Type* Reserve, **Preview** | "18 location(s) will be created.": R-A-01-1, R-A-01-2 … R-B-03-3. Nada é gravado ainda. |
| **Create** | 18 locations na lista da aba, na ordem de picking (10, 20, 30…). |
| **Create** de novo com os mesmos valores | Nenhuma nova: as 18 aparecem como já existentes. |
| *Aisle* de A até Z, *Rack* 01 até 99, *Level* 1 até 9 | Recusado: "Too many locations at once (2000 at most): make smaller ranges." |
| *Rack* de 03 até 01 | Recusado: "Invalid range: … the first one not after the last." |
| **New location** (na aba): QUAI, "Quai de réception", *Type* Receiving, aceita produtos misturados | Volta para a aba *Locations* do MP com QUAI na lista. **Back** de uma location sempre volta para o depósito. |
| Aba *General* do MP: *Receiving location* QUAI, **Save** | Gravado. |
| INT: *Zone* T, *Aisle* A, *Rack* 01 até 04, sem *Level*, *Type* Picking | 4 locations: T-A-01 a T-A-04. *Receiving location* T-A-01. |
| PF: *Zone* F, *Aisle* A até B, *Rack* 01 até 04, *Level* 1 até 2, *Type* Reserve | 16 locations: F-A-01-1 a F-B-04-2. |
| PF: **New location** EXPED, "Quai d'expédition", *Type* Shipping | *Shipping location* EXPED, *Receiving location* F-A-01-1. |
| Depósito com mais de 10 locations | Aparece a caixa de busca: digitar "B-02" filtra a lista. |

## 7. Fornecedores

**Accounts Payable > Suppliers**, todos em QC, CA, *Payment term* n30 (net 30 jours):

| Code | Name | Endereço | TPS number | TVQ number |
|---|---|---|---|---|
| FERME-ORLEANS | Ferme de l'île d'Orléans | 1830, chemin Royal, Saint-Laurent-de-l'Île-d'Orléans, G0A 3Z0 | 811111111RT0001 | 1211111111TQ0001 |
| SUCRES-LAUR | Sucres Laurentiens inc. | 500, rue des Raffineurs, Montréal, H1B 2C3 | 822222222RT0001 | 1222222222TQ0001 |
| EMBAL-QC | Emballages Québec ltée | 75, rue Industrielle, Saint-Hyacinthe, J2R 1C4 | 833333333RT0001 | 1233333333TQ0001 |

## 8. Produtos

**Inventory > Products**. Todos físicos, estocados, custo médio, CAD. Os com lote têm *Lot numbers* e validade marcados, *Stock out order* FEFO.

| Code | Class | Cat. | Description (FR / EN) | Unit | Warehouse | Tax | Lote / validade (dias) | Fornecedor e preço | GL |
|---|---|---|---|---|---|---|---|---|---|
| FRAISE-IQF | Raw material | RAW | Fraises surgelées IQF / Frozen IQF strawberries | KG | MP | ZERO | sim / 365 | FERME-ORLEANS 4,20 | compra 5100, estoque 1310 |
| SUCRE | Raw material | RAW | Sucre granulé / Granulated sugar | KG | MP | ZERO | sim / 730 | SUCRES-LAUR 1,10 | 5100 / 1310 |
| PECTINE | Raw material | RAW | Pectine de pomme / Apple pectin | KG | MP | ZERO | sim / 730 | SUCRES-LAUR 18,00 | 5100 / 1310 |
| POT-250 | Raw material | PACK | Pot en verre 250 ml / Glass jar 250 ml | UN | MP | QC | não | EMBAL-QC 0,38 | 5110 / 1310 |
| COUV-63 | Raw material | PACK | Couvercle 63 mm / Lid 63 mm | UN | MP | QC | não | EMBAL-QC 0,09 | 5110 / 1310 |
| ETIQ-CONF | Raw material | PACK | Étiquette confiture / Jam label | UN | MP | QC | não | EMBAL-QC 0,04 | 5110 / 1310 |
| SACHET-200 | Raw material | PACK | Sachet refermable 200 g / Resealable pouch 200 g | UN | MP | QC | não | EMBAL-QC 0,12 | 5110 / 1310 |
| PUREE-FRAISE | Kit/Assembly | WIP | Purée de fraises cuite / Cooked strawberry puree | KG | INT | ZERO | sim / 30 | (não se compra) | estoque 1320 |
| CONF-FRAISE-250 | Finished product | FG | Confiture de fraises, pot 250 ml / Strawberry jam, 250 ml jar | UN | PF | ZERO | sim / 540 | preço de venda 4,25 | venda 4100, estoque 1330, CPV 5200 |
| PATE-FRUIT-200 | Finished product | FG | Pâtes de fruits aux fraises, sachet 200 g / Strawberry fruit jellies, 200 g pouch | UN | PF | QC | sim / 365 | preço de venda 5,50 | 4200 / 1330 / 5200 |

| Passo | Esperado |
|---|---|
| Lista | 10 produtos. |
| Num produto, *GL - inventory* 9999 | Só aceita contas que existem (lista do plano de contas). |

## 9. Chão de fábrica e receitas

**Production > Calendars**: USINE-1X5, "Usine : 1 équipe, lundi au vendredi", segunda a sexta, turno JOUR 07:00–15:30, 30 min de pausa.

**Production > Work centers**:

| Code | Descrição | Type | Warehouse | Taxa setup/run (h) | Burden (h) | Cost center |
|---|---|---|---|---|---|---|
| CUISSON | Marmites de cuisson / Cooking kettles | Machine | INT | 40 | 15 | 200-210 |
| REMPLISSAGE | Ligne de remplissage / Filling line | Machine | PF | 35 | 15 | 200-220 |

**Production > Standard operations** (todas *min per lot*, ponto de apontamento):

| Code | Descrição | Work center | Setup (min) | Run (min) | Crew |
|---|---|---|---|---|---|
| CUIRE | Cuire la purée / Cook the puree | CUISSON | 20 | 90 | 1 |
| REMPLIR | Remplir et capsuler les pots / Fill and cap the jars | REMPLISSAGE | 15 | 60 | 2 |
| MOULER | Couler, sécher et ensacher / Pour, dry and bag | REMPLISSAGE | 15 | 120 | 2 |

**Production > Manufactured items**: PUREE-FRAISE, CONF-FRAISE-250 e PATE-FRUIT-200 com *Make or buy* = Make e rastreio por lote.

**Production > Recipes**, revisão A, *Batch*, depois **Submit** e **Approve**:

| Receita | Base | Materiais (operação 10) | Passos |
|---|---|---|---|
| PUREE-FRAISE | 100 KG | FRAISE-IQF 105 KG, manual, do MP. Nota: "100 kg de purée : 105 kg de fraises (5 % d'évaporation)." | 10 *Material add* "Verser les fraises (lire le lot)"; 20 *Measure* "Température de cuisson (85 °C ou plus)", TEMP_CUISSON °C, alvo 90, mín. 85, máx. 98, obrigatório, **crítico**, fora do limite **segura o lote** |
| CONF-FRAISE-250 | 100 UN | PUREE-FRAISE 15 KG (do **INT**), SUCRE 12 KG, PECTINE **300 G** (manual, do MP); POT-250, COUV-63, ETIQ-CONF 100 UN cada em *backflush* | 10 *Measure* "Brix de la confiture (61 à 65)", BRIX, alvo 63, crítico, **bloqueia**; 20 *Check* "Pots bien scellés", crítico, bloqueia |
| PATE-FRUIT-200 | 100 UN | PUREE-FRAISE 10 KG (INT), SUCRE 11 KG, PECTINE 600 G; SACHET-200 100 UN em *backflush* | — |

| Passo | Esperado |
|---|---|
| PECTINE em G, sendo o estoque em KG | Aceito por causa da conversão 1 KG = 1000 G (na ordem vira 0,3 KG). |
| Custo da receita PUREE-FRAISE (100 KG) | Materiais 441,00 $ (105 × 4,20), operações 95,83 $, total 536,83 $ = 5,3683 / KG. |
| Lista de receitas | As três *Approved*. |

## 10. Compras e recepções

**Purchasing > Purchase orders** (data 2026-11-30):

| PO | Fornecedor | Linhas | Subtotal |
|---|---|---|---|
| PO-1001 | FERME-ORLEANS | FRAISE-IQF 400 KG × 4,20 | 1 680,00 $ |
| PO-1002 | SUCRES-LAUR | SUCRE 500 KG × 1,10; PECTINE 10 KG × 18,00 | 730,00 $ |
| PO-1003 | EMBAL-QC | POT-250 1200 × 0,38; COUV-63 1200 × 0,09; ETIQ-CONF 1200 × 0,04; SACHET-200 600 × 0,12 | 684,00 $ |

**Purchasing > Receptions** (data 2026-12-01, *Warehouse* MP). Digite a location e o lote do fornecedor em cada linha:

| Reception | PO | Linhas (location, lote do fornecedor) |
|---|---|---|
| 700001 | PO-1001 | FRAISE-IQF 200 KG em R-A-01-1 (IO-2611-A) e mais 200 KG em R-A-01-2 (IO-2611-B) |
| 700002 | PO-1002 | SUCRE 500 KG em R-A-02-1 (SL-88231); PECTINE 10 KG em R-A-02-2 (PC-5512) |
| 700003 | PO-1003 | POT-250 em R-B-01-1, COUV-63 em R-B-01-2, ETIQ-CONF em R-B-01-3, SACHET-200 em R-B-02-1 |

| Passo | Esperado |
|---|---|
| Linha da recepção: *Department* 999 | "Unknown or inactive cost center on a line". O campo só lista centros ativos; *Sub-department* só lista os do departamento escolhido. |
| **Check** da 700001 | Sem problemas: lotes 700001-1 e 700001-2, validade 2027-12-01 (365 dias), 4,20 $/KG. |
| **Post** das três | Entram no estoque. |
| **Inventory > Stock on hand** | Cada lote na sua location: FRAISE-IQF 200 em R-A-01-1 e 200 em R-A-01-2, SUCRE 500, PECTINE 10, potes, tampas e etiquetas 1200, sachets 600. |
| **Inventory > Products**, FRAISE-IQF | Custo médio **4,20 $** (as duas linhas do mesmo produto na mesma recepção mantêm a média). |
| **Inventory > Inventory valuation** | 3 094,00 $ (1 680 + 730 + 684). |

## 11. Fatura de fornecedor: conta e centro de custo

**Accounts Payable > Invoices**, **New**, fornecedor SUCRES-LAUR, uma linha de despesa sem produto (ex.: "Réparation brûleur", 1 × 250,00):

| Passo | Esperado |
|---|---|
| *GL* 5700 sem centro de custo, **Save** | "This GL account requires a cost center on the line" (linha 1). |
| *GL* 9999 | "Unknown or inactive GL account on a line". |
| *Department* 200, *Sub-department* 210 | Gravado. A lista de *Sub-department* mostra só 210 e 220. |
| Desativar o centro 500 (*Active* desmarcado) e abrir a lista *Department* numa linha | O 500 não aparece mais. Reative depois. |

## 12. Produção da purée (INT) e o desvio de temperatura

**Production > Production orders**, **New**: PUREE-FRAISE 100 KG, *Warehouse* INT, início e prazo 2026-12-02.

| Passo | Esperado |
|---|---|
| Card *Materials* | FRAISE-IQF 105 KG do MP. Custo estimado 536,83 $ (5,3683 / KG). |
| **Save**, **Release**, **Show the lots** | 105 KG do lote 700001-1 (R-A-01-1). |
| **Issue** | Materiais consumidos. |
| Passo 10 (verser) e passo 20 temperatura **92** | Dentro do limite. |
| **Report**: *Quantity made* 100, *Location* T-A-01 | Lote MO&lt;n&gt; (ex.: MO16), validade 30 dias, custo 5,3683 / KG. |
| **Complete** e **Close** | Custo real 536,83 $: materiais 441,00 + operações 95,83. |
| Segunda ordem igual; temperatura **81** com o comentário "Brûleur 2 en panne"; *Quantity made* 98 em T-A-02 | O passo fica fora do limite e o lote novo vai **automaticamente para *On hold***. Os lotes usados: 95 KG do 700001-1 e 10 KG do 700001-2 (FEFO). Custo real 534,91 $ = 5,4583 / KG (98 KG feitos). |
| **Quality > Lot status** | O lote da 2ª ordem *On hold*, motivo "Order &lt;n&gt;, step 10/20 Cooking temperature (85 °C or more): 81 °C". |

## 13. Qualidade: não conformidade

**Quality > Nonconformances**, **New**:

| Campo | Valor |
|---|---|
| *Source* / *Ref* | Production / o lote da 2ª ordem |
| *Product* / *Lot* / *Qty* | PUREE-FRAISE / MO&lt;n&gt; / 98 KG |
| *Severity* | Major |
| *Description* | Température de cuisson 81 °C (minimum 85 °C). |
| *Cause* | Brûleur 2 en panne. |
| *Disposition* | Scrap |
| *Action* | Brûleur réparé; vérification du brûleur ajoutée à l'entretien hebdomadaire. |

| Passo | Esperado |
|---|---|
| **Save** | NC aberta, com número. |
| **Quality > Lot status**, o lote, mudar para *Rejected* com o motivo "NC &lt;n&gt; : cuisson à 81 °C, lot détruit." | Histórico: Released → On hold → Rejected. |
| **Close** da NC | *Closed*, *Disposition* Scrap. |

## 14. Produtos finais (PF)

| Ordem | Passos | Esperado |
|---|---|---|
| CONF-FRAISE-250 100 UN, *Warehouse* PF | Materiais | PUREE-FRAISE 15 KG do INT, SUCRE 12 KG, PECTINE 0,3 KG, potes, tampas e etiquetas 100 UN. Custo estimado 208,87 $. |
| | **Show the lots** | A purée sai do lote **bom** (o da 1ª ordem, em T-A-01). O lote rejeitado nunca é usado. |
| | **Issue**; Brix 60 sem comentário | "The value is out of its limits: write the corrective action". Com o comentário "Trop liquide" grava, mas o **Report** recusa: "A critical step is out of its limits: record it again within its limits first". |
| | Brix 63; *Pots bien scellés* = Yes; **Report** 100 em F-A-01-1 | Lote MO&lt;n&gt;, validade 540 dias. Potes, tampas e etiquetas saem sozinhos (*backflush*). |
| | **Complete**, **Close** | Real 208,87 $: materiais 150,12 + operações 58,75 = 2,0887 / UN. |
| PATE-FRUIT-200 100 UN, PF | **Report** 100 em F-B-01-1 | Real 197,33 $: materiais 88,58 + operações 108,75 = 1,9733 / UN. |
| **Inventory > Stock on hand**, depósito PF | | Geleia 100 em F-A-01-1, pâtes de fruits 100 em F-B-01-1. No INT: purée boa 75 KG (100 − 15 − 10) e a rejeitada 98 KG. No MP: FRAISE-IQF 190 KG (lote 700001-2), SUCRE 477, PECTINE 9,1, potes/tampas/etiquetas 1100, sachets 500. |

## 15. Clientes e lista de preços

**Sales > Price lists**: GROCERS, Épiceries / Grocers: CONF-FRAISE-250 3,95 a partir de 1 e **3,75 a partir de 48**; PATE-FRUIT-200 4,95.

**Sales > Customers**:

| Code | Name | Idioma | Endereço | Tax group | Price list | Warehouse |
|---|---|---|---|---|---|---|
| EPICERIE-BEAUCE | Épicerie de la Beauce | French | 120, avenue du Palais, Saint-Joseph-de-Beauce, QC, G0S 2V0 | QC | GROCERS | PF |
| CAFE-VIEUX-QC | Café du Vieux-Québec | English | 35, rue Saint-Louis, Québec, QC, G1R 3Z2 | QC | (nenhuma) | PF |

## 16. Vendas, impressão com logo e nota de crédito

**Sales > Invoices** (data 2026-12-03):

| Fatura | Linhas | Esperado |
|---|---|---|
| EPICERIE-BEAUCE | 48 confitures + 24 pâtes de fruits | Confiture 3,75 (lista, faixa de 48), sem imposto (ZERO) = 180,00; pâtes 4,95 com QC = 118,80. Subtotal 298,80, TPS 5,94, TVQ 11,85, **total 316,59 $**. |
| | **Check** | Sai do lote da geleia em F-A-01-1 e do lote das pâtes em F-B-01-1. |
| | **Post** | Número **5001**. Custo 147,62 $. |
| | **Print** | Logo no canto da fatura, ao lado do nome da empresa; texto em francês; números de TPS e TVQ; nota da fatura. |
| CAFE-VIEUX-QC | 12 confitures + 6 pâtes | Preço do produto (4,25 e 5,50): 51,00 + 33,00 = 84,00, TPS 1,65, TVQ 3,29, **total 88,94 $**. **Post**: número **5002**. **Print** em inglês, com o logo. |
| Na 5001, **Credit** | Deixar só a confiture, quantidade 2, sem *Return to stock* (potes quebrados) | Total 7,50 $ sem imposto. **Post**: NC-&lt;n&gt;. |
| **Inventory > Stock on hand**, PF | | Geleia 40 (100 − 48 − 12), pâtes 70 (100 − 24 − 6). |

## 17. Rastreabilidade até o fornecedor (com logo no Excel)

**Production > Lots and traceability**

| Passo | Esperado |
|---|---|
| FRAISE-IQF, lote 700001-1 | *Origin*: recepção 700001, PO-1001, FERME-ORLEANS, lote do fornecedor IO-2611-A. Movimentos: entrada 200, saídas 105 e 95 para as duas ordens de purée. |
| *Uses* / *Customers* | A purée dos dois lotes, a geleia e as pâtes, e os clientes EPICERIE-BEAUCE e CAFE-VIEUX-QC (recall). |
| Lote da geleia | Volta à purée boa e daí à fraise 700001-1 e ao fornecedor. |
| **Export** (Excel) | A planilha *Summary* abre com o **logo** no topo, acima do resumo. |

## 18. Ajuda das telas

| Passo | Esperado |
|---|---|
| **?** em *System settings* | Item *Logo*. |
| **?** em *Warehouses / locations* | Aba *Locations*, busca, gerador (*Zone*, *Aisle*, *Rack*, *Level*, *Bin*, de/até, prévia). |
| **?** em *GL Accounts / Cost Centers* | Explica *Type*, *Requires a cost center*, departamento e subdepartamento, e que conta e centro de custo se encontram só nas linhas de compra. |
| Botão **FR** | Mesmas ajudas em francês. |
