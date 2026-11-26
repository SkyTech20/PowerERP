# PowerERP — Indicadores da cadeia de suprimentos (SCOR): roteiro de testes

> **Atenção:** este roteiro foi escrito para o cenário *Pastry shop*, que foi removido (o padrão agora é *Maple products*, veja PowerERP-Demo-Bordo-Roteiro-Testes.md). Ele será refeito com os produtos de bordo; até lá, os códigos e números citados aqui não existem no demo.

Roteiro para testar a tela **Reports > Supply chain indicators** (passo 7 do plano SCOR / ISO: atributos de desempenho SCOR, ISO 9001 9.1 monitoramento e medição). A tela não tem nada para digitar: cada número vem das faturas, recepções, ordens de produção, registros do chão de fábrica, não conformidades e movimentos de estoque do ERP. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Pastry shop** depois dos preparativos da seção 1, feitos no mesmo dia.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo.

---

## 1. A tela com os dados do demo

**Reports > Supply chain indicators** (item novo no menu **Reports**)

| Passo | Esperado |
|---|---|
| Abrir a tela | Filtros no alto: *Period* "Last 90 days", *From* (hoje − 89 dias), *To* hoje, *Lots expiring within* "30 days", e "90 days" à direita. Quatro grupos de cartões: *Reliability* (6), *Responsiveness* (2), *Cost* (2), *Assets* (5). |
| Cartões sem dados (ex.: *Perfect orders*, *Production on time*) | Um traço "—" e "No data in the period": o demo ainda não tem fatura postada nem ordem terminada. |
| *Supplier fill rate* e *Receptions without a problem* | 100 %: tudo o que foi pedido foi recebido e nenhuma recepção tem não conformidade. |
| *Stock value* | O mesmo total de **Inventory > Inventory valuation**. |
| *Lots to expire* e o card *Lots to watch* | O ovo EGG 900103-1 (validade 2026-12-25) aparece quando faltam 30 dias ou menos; com o selo "N day(s) left". Trocar *Lots expiring within* para 7 days: some da lista se faltar mais de 7 dias. |
| Card *Stock by product* | Os produtos em estoque; os que não saíram no período vêm primeiro com o selo *Not used*. |
| **?** | Abre a ajuda da tela; os filtros têm seu **?**. |

## 2. Preparar: vender, fabricar, achar um problema

| Passo | Esperado |
|---|---|
| **Sales > Invoices**: abrir as faturas rascunho 1, 2 e 3 e **Post** em cada uma | Três faturas postadas. |
| Na fatura 1 postada, **Credit note** e **Post** da nota de crédito | Uma nota de crédito que credita a fatura 1. |
| **Production > Production orders**, **New**: DOUGH, 10 KG, *Start* 5 dias atrás, *Due* amanhã, **Save**, **Release**, **Issue** | Ordem em andamento. |
| Card *Recipe steps*: *Add warm water* 3,6, **Record**; *Shop floor*: **Report** 9,8; **Complete**; **Close** | Ordem fechada no prazo, 9,8 de 10. |
| **New**: PASTEL-HAM-CHEESE, 40 UN, *Start* 5 dias atrás, *Due* 2 dias atrás, **Save**, **Release**, **Issue** | Ordem em andamento. |
| *Oil temperature* 190 com a ação corretiva "Fogo baixado", **Record**; depois 180, **Record**; **Report** 38; **Complete** | Ordem terminada com atraso, 38 de 40, um desvio. |
| **Quality > Nonconformances**, **New**: *Found at* Reception, *Document* 900104, *Severity* Major, HAM 900104-1, "Temperatura alta na recepção", **Save** | NC aberta, lote HAM segurado. |

## 3. Os indicadores depois

**Reports > Supply chain indicators**

| Passo | Esperado |
|---|---|
| *Perfect orders* | 66,7 %, "2 of 3 invoices" (a fatura 1 tem nota de crédito). |
| *Production on time* | 50 %, "1 of 2 orders" (a ordem do pastel passou do prazo). |
| *Production yield* | 95,6 %, "47.80 made of 50.00 ordered". |
| *Receptions without a problem* | 83,3 %, "5 of 6 receptions" (a recepção 900104 tem a NC). |
| *Steps right first time* | 66,7 %, "2 of 3 records" (o 190 °C). |
| *Production cycle time* | Os dias entre o **Release** e o **Complete** (0,0 se foi no mesmo dia). |
| *Time to close a nonconformance* | "—": nenhuma NC fechada ainda. Fechar a NC (decisão + ação corretiva) e voltar: aparecem os dias. |
| *Production cost variance* | O % do custo real contra o estimado da ordem fechada (DOUGH). |
| *Gross margin* | (vendas − custo) / vendas das faturas postadas, menos a nota de crédito. |
| *Stock turns* e *Days of supply* | Agora com valor: o estoque saiu para as faturas e para as ordens. |
| *Lots held back* | O valor do HAM 900104-1, "1 lot(s) on hold...". No card *Lots to watch*, em *Held back by quality*, HAM 900104-1 *On hold*. Clicar a linha abre o rastreio do lote. |
| Card *Nonconformances* | "1 found in the period", "1 open today"; barras *Reception* 1 e *Major* 1. |
| Card *Deviations on the shop floor* | A linha da ordem do pastel: *20/10 Oil temperature*, 190 °C *Above the maximum*, *warning*, "Fogo baixado", admin. Clicar abre a ordem. |
| Card *Stock by product* | Os produtos usados agora têm *Used in the period* e *Days of supply*; os outros continuam *Not used*. |
| Clicar o cartão *Gross margin* | Abre **Sales > Invoices**. Cada cartão abre a tela de onde vem. |

## 4. Período e permissões

| Passo | Esperado |
|---|---|
| *Period* "Last 30 days", "Last 12 months", "This year" | As datas mudam e os números são recalculados. |
| *From* depois de *To* | Aviso "The start of the period is after its end." |
| Um período antigo (ex.: 2025) | Tudo "—" nos cartões do período; *Stock value* e os lotes continuam (são de hoje). |
| **Administration > Roles**: um perfil sem *Supply chain indicators* | O item some do menu de quem tem esse perfil. Com *View*, aparece. Os perfis de demo PRODUCTION e WAREHOUSE já têm. |
| Tela no celular (largura estreita) | Os cartões ficam um embaixo do outro, sem rolagem lateral. |
