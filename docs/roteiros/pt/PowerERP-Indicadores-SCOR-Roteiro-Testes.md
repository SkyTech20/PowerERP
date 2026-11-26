# PowerERP — Indicadores da cadeia de suprimentos (SCOR): roteiro de testes

Roteiro para testar a tela **Reports > Supply chain indicators** (passo 7 do plano SCOR / ISO: atributos de desempenho SCOR, ISO 9001 9.1 monitoramento e medição). A tela não tem nada para digitar: cada número vem das faturas, recepções, ordens de produção, registros do chão de fábrica, não conformidades e movimentos de estoque do ERP. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. Os valores esperados são os do cenário **Maple products** logo depois de restaurar o demo, com o período de 90 dias até 26/11/2026.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Maple products** e restaure os dados de demo. O demo traz outubro e novembro de 2026; se hoje for depois de 26/11/2026, coloque *From* 2026-08-29 e *To* 2026-11-26 para ver os mesmos números. Os lotes a vencer contam sempre a partir de hoje.

---

## 1. A tela com os dados do demo

**Reports > Supply chain indicators**

| Passo | Esperado |
|---|---|
| Abrir a tela | Filtros no alto: *Period* "Last 90 days", *From* (hoje − 89 dias), *To* hoje, *Lots expiring within* "30 days", e "90 days" à direita. Quatro grupos de cartões: *Reliability* (6), *Responsiveness* (2), *Cost* (2), *Assets* (5). Todos os cartões têm valor. |
| *Perfect orders* | 88,9 %, "8 of 9 invoices" (a fatura 5 tem a nota de crédito NC-1). |
| *Production on time* | 90,9 %, "10 of 11 orders" (a ordem 9 dos bonbons terminou um dia depois do prazo). |
| *Production yield* | 99,7 %, "6,184.00 made of 6,200.00 ordered" (796 latas de 800 e 388 caixas de bala de 400). |
| *Supplier fill rate* | 99,9 % (o barril T-118 veio com 266 kg de 280). |
| *Receptions without a problem* | 85,7 %, "6 of 7 receptions" (a recepção 900106 tem a NC do barril T-140). |
| *Steps right first time* | 97,6 %, "41 of 42 records" (o 118,5 °C da ordem 9). |
| *Production cycle time* | 0,51 dia entre o **Release** e o **Complete**, na média das 11 ordens. |
| *Time to close a nonconformance* | 3,21 dias (média das NCs 1 e 2). |
| *Production cost variance* | 0,1 % do custo real contra o estimado das ordens fechadas. |
| *Gross margin* | 43,3 %: (vendas − custo) / vendas das faturas postadas, menos a nota de crédito. |
| *Stock value* | 11 966,96 $, o mesmo total de **Inventory > Inventory valuation**. |
| *Stock turns* e *Days of supply* | 14,92 voltas e 24,47 dias. |
| *Lots held back* | 681,20 $, "1 lot(s) on hold, in quarantine or rejected": os bonbons MO9. No card *Lots to watch*, em *Held back by quality*, MAPLE-CANDY-12 MO9 *On hold*. Clicar a linha abre o rastreio do lote. |
| *Lots to expire* e o card *Lots to watch* | 160,30 $: a crème CREAM-35 900105-1 já vencida em 2026-10-27, a crème 900107-1 (2026-12-01) e o beurre BUTTER 900105-2 (2026-12-05), cada uma com o selo "N day(s) left" (a vencida com *Expired*). Trocar *Lots expiring within* para 7 days: o beurre some (se faltar mais de 7 dias). |
| Card *Nonconformances* | "3 found in the period", "1 open today"; barras *Reception* 1, *Production* 1, *Customer* 1, *Major* 2, *Minor* 1. |
| Card *Deviations on the shop floor* | A ordem 9: *10/20 Cook to 115 °C*, 118,5 °C *Above the maximum*, *the lot is held*, "Sonde du cuiseur 2 décalée...", admin. Clicar abre a ordem. |
| Card *Stock by product* | Os produtos em estoque; os que não saíram no período vêm primeiro com o selo *Not used* (GLOVES). Os outros mostram *Used in the period* e *Days of supply*. |
| **?** | Abre a ajuda da tela; os filtros têm seu **?**. |

## 2. Mexer nos dados e ver os indicadores mudarem

| Passo | Esperado |
|---|---|
| **Sales > Invoices**, rascunho de DISTRIB-CHAUDIERE, **Post** | Fatura 10 postada. |
| **Quality > Nonconformances**, abrir a 3 (MAPLE-CANDY-12 MO9), *Disposition* Scrap, *Root cause* "Probe of cooker 2 out of calibration.", *Corrective action* "Probe recalibrated; check it every Monday.", **Close** | NC fechada; o lote MO9 passa a *Rejected*. |
| **New**: *Found at* Reception, *Document* 900107, *Severity* Minor, CREAM-35 900107-1, *Quantity affected* 12, "Cream delivered at 7 °C, limit 4 °C", **Save** | NC 4 aberta, lote da crème segurado. |
| Voltar para **Reports > Supply chain indicators** | *Perfect orders* 90 %, "9 of 10 invoices". *Receptions without a problem* 71,4 %, "5 of 7". *Gross margin* 42,6 %. *Stock value* 10 573,67 $ (saiu o custo da fatura 10); *Stock turns* 17,42 e *Days of supply* 20,96. |
| *Time to close a nonconformance* | Sobe: a NC 3 ficou aberta desde 06/11 até hoje e entra na média. |
| *Lots held back* | 755,60 $, 2 lotes: MO9 *Rejected* (rejeitado continua fora de venda) e a crème 900107-1 *On hold*. |
| Card *Nonconformances* | "4 found in the period", "1 open today"; *Reception* 2, *Minor* 2. |
| Clicar o cartão *Gross margin* | Abre **Sales > Invoices**. Cada cartão abre a tela de onde vem. |

## 3. Período e permissões

| Passo | Esperado |
|---|---|
| *Period* "Last 30 days", "Last 12 months", "This year" | As datas mudam e os números são recalculados. Com 30 dias, as ordens e faturas de outubro saem da conta. |
| *From* depois de *To* | Aviso "The start of the period is after its end." |
| Um período antigo (ex.: 2025) | Tudo "—" e "No data in the period" nos cartões do período; *Stock value* e os lotes continuam (são de hoje). |
| **Administration > Roles**: um perfil sem *Supply chain indicators* | O item some do menu de quem tem esse perfil. Com *View*, aparece. Os perfis de demo PRODUCTION e WAREHOUSE já têm. |
| Tela no celular (largura estreita) | Os cartões ficam um embaixo do outro, sem rolagem lateral. |
