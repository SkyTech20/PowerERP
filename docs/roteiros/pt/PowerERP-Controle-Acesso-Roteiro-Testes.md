# PowerERP — Controle de acesso: roteiro de testes (A1 a A3)

Roteiro para testar os perfis (*Roles*) no demo. Os rótulos de tela estão em inglês, como aparecem no ERP com o botão **EN**. O manual da tela está na ajuda do ERP (Help > Administration > Roles).

**Antes de começar:**

1. Entre como administrador e vá em **Administration > System settings**.
2. Restaure os dados de demo. Isso recoloca os perfis de exemplo SALES, PRODUCTION e WAREHOUSE.
3. Usuários e perfis criados por você não são apagados pelo demo, então dá para repetir o roteiro.

Use duas janelas: uma normal com o administrador, e uma anônima (ou outro navegador) para entrar com os outros usuários.

---

## 1. Lista de perfis

**Administration > Roles**

| Passo | Esperado |
|---|---|
| Abrir a tela | Aparecem ADMIN, PRODUCTION, SALES, USER e WAREHOUSE. ADMIN mostra *All* em Screens. SALES abre 6 telas, WAREHOUSE 8 e PRODUCTION 11. |
| Abrir ADMIN | Abre só para leitura, com o aviso *The administrator role has every permission and cannot be changed*. Não tem Save nem Delete. |

## 2. Níveis por tela (aba Access)

Abra **SALES**.

| Passo | Esperado |
|---|---|
| Ver os módulos à esquerda | Sales mostra *3 of 3*. Inventory mostra *2 of 9* (Products e Stock on hand). Administration mostra *View* (só Taxes). Os outros módulos mostram *No access*. |
| Clicar em **Sales** | Customers = **Edit**, Price lists = **View**, Invoices = **Custom** (tudo menos Credit note). |
| Em Invoices, clicar em **Customize** | Aparecem as ações View, Create, Edit, Delete, Post, Credit note e Print. Só Credit note está desmarcada. |
| Marcar **Credit note** | O nível de Invoices passa a **Full**. |
| Desmarcar **View** | Todas as ações de Invoices são desmarcadas e o nível vira **No access**. |
| Clicar em **Full** de novo em Invoices e depois em **Cancel** | Nada é salvo. Reabrindo SALES, Invoices continua **Custom**. |
| Abrir Inventory e clicar em **Set all screens: View** | Todas as telas de Inventory ficam em **View**. *Stock on hand* e *Inventory valuation* só oferecem No access e View. Clique em **Cancel**. |

## 3. Preview menu

Ainda em SALES:

| Passo | Esperado |
|---|---|
| Clicar em **👁 Preview menu** | Mostra Sales (Customers, Price lists, Invoices), Inventory (Products, Stock on hand) e Administration (Taxes). |
| Fechar, colocar Production > Recipes em View e abrir o Preview de novo | Production > Recipes aparece no menu, mesmo sem salvar. Clique em **Cancel**. |

## 4. Criar um perfil copiando outro

**Administration > Roles > New**

| Passo | Esperado |
|---|---|
| Code `buyer`, Description (French) `Acheteur`, Description (English) `Buyer` | O código vira BUYER (maiúsculas). |
| Code `com espaço` e Save | O sistema recusa: *Use capital letters, digits, - or _*. Volte para BUYER. |
| *Copy from role* = WAREHOUSE | As permissões de WAREHOUSE aparecem na aba Access. |
| Purchasing > **Set all screens: Full** e Save | O perfil é salvo e abre. Purchase orders e Receptions ficam em **Full**. |
| Criar de novo com o Code BUYER | O sistema recusa porque o código já existe. |
| Aba **History** do BUYER | Uma linha *Created* com *Copied from WAREHOUSE*. |

## 5. Histórico de mudanças

Abra **SALES**.

| Passo | Esperado |
|---|---|
| Sales > Invoices: marcar **Credit note** e Save | Salvo. |
| Mudar Description (English) para `Sales counter` e Save | Salvo. |
| Aba **History** | No topo, *Description / status* com o valor antigo e o novo, e *Permissions* com *+ Sales › Invoices: Credit note*. Cada linha mostra a data, a hora e o usuário admin. |
| Desmarcar Credit note, voltar a descrição para `Sales desk` e Save | Novas linhas no histórico com a permissão retirada (−). |

## 6. Usuários e perfil

**Administration > Users & security**

| Passo | Esperado |
|---|---|
| Criar `marie` (Name Marie Lefebvre, Role **SALES**, senha `secret1`) | Salvo. O campo Role lista só perfis ativos. |
| Criar `paul` (Name Paul Roy, Role **WAREHOUSE**, senha `secret1`) | Salvo. |
| Criar `luc` (Name Luc Gagnon, Role **PRODUCTION**, senha `secret1`) | Salvo. |
| **Roles > SALES**, aba **Users** | Mostra marie. |
| Tentar apagar SALES | O sistema recusa porque o perfil tem usuários. |
| Apagar BUYER (sem usuários) | Apagado. Não aparece mais na lista. |

## 7. Usuário de vendas (marie)

Entre como **marie / secret1** na janela anônima.

| Passo | Esperado |
|---|---|
| Ver o menu | Só Dashboard, Sales (Customers, Price lists, Invoices), Inventory (Products, Stock on hand) e Administration (Taxes). Sem General Ledger, Accounts Payable, Purchasing e Production. |
| Ver o Dashboard | Não mostra nenhum número (fornecedores, compras e valor de estoque são de telas fora do perfil). Aparece *Your role shows no figures here: open your screens from the menu*. |
| **Sales > Invoices** | O botão **New** aparece. |
| Abrir o rascunho #3 | Tem **Save**, **Delete**, **Check**, **Post** e **Print**. |
| Clicar em **Post** no rascunho #3 | A invoice é postada e recebe número. Ela tem **Print**, mas não tem **Credit note**. |
| **Sales > Price lists** e abrir uma tabela | Sem **New** na lista. O formulário abre só para leitura, só com *Back to list*. |
| **Sales > Customers** e abrir um cliente | Tem **Save**, mas não tem **Delete**. |
| Na barra de endereço, trocar o final para `#/po` | Volta para o Dashboard (Purchase orders não está no perfil). |
| **Inventory > Products** | Sem **New**. O produto abre só para leitura. |

## 8. Usuário de depósito (paul)

Entre como **paul / secret1**.

| Passo | Esperado |
|---|---|
| Ver o menu | Inventory (Products, Stock on hand, Stock movements, Replenishment, Physical count, Warehouses / locations, Reorder parameters) e Purchasing (Receptions). Sem Sales. |
| **Inventory > Replenishment** | Mostra as sugestões, mas sem o botão **Create purchase orders** (o admin vê esse botão). |
| **Inventory > Physical count > New**, escolher ENT-01 e Save | A contagem é criada e tem **Refresh from stock**, **Post the count** e **Save**. Não tem **Delete** (o admin vê Delete na mesma contagem). |
| **Inventory > Reorder parameters** | Pode alterar e salvar. Sem **New**. |

## 9. Usuário de produção (luc)

Entre como **luc / secret1**.

| Passo | Esperado |
|---|---|
| Ver o menu | Production inteiro, mais Inventory (Products, Stock on hand, Categories / units). |
| **Production > Recipes** | Tem **New**. |
| Abrir PAIN-BL-675 versão B (*In review*) | Só tem *Back to list* e *New version from this one*. Não tem **Approve** nem **Send back**. |
| Como admin: **Roles > PRODUCTION**, Production > Recipes em **Full**, Save | Salvo. |
| Como luc: recarregar a página e abrir a mesma receita | Agora aparecem **Approve** e **Send back**. Não aprove: volte ao admin. |
| Como admin: voltar Recipes para **Edit** e Save | O histórico mostra as duas mudanças. |

## 10. Perfil inativo

| Passo | Esperado |
|---|---|
| Como admin: **Roles > WAREHOUSE**, desmarcar **Active** e Save | Aparece o aviso *Inactive: its users open no screen*. |
| Como paul: recarregar a página | O menu mostra só o Dashboard, com *Your role shows no figures here*. |
| Como admin: marcar **Active** de novo e Save | Paul volta a ver as telas ao recarregar. |

## 11. Bloqueio no servidor

Este teste confere que o bloqueio não depende só de esconder o botão.

| Passo | Esperado |
|---|---|
| Como marie, abrir `http://<servidor>:5051/api/purchase-orders` no navegador | Resposta 403 (*forbidden*). |
| Como marie, abrir `.../api/roles` | Resposta 403: só o administrador gerencia perfis. |
| Como admin, os mesmos endereços | Respondem com os dados. |

## 12. Demo de volta

| Passo | Esperado |
|---|---|
| Como admin: **System settings**, restaurar o demo | SALES, PRODUCTION e WAREHOUSE voltam às permissões do exemplo. |
| Antes de restaurar: em **Roles > SALES**, marque Credit note em Invoices e salve | Salvo. |
| Restaurar o demo e abrir **Roles > SALES > History** | Uma linha *Demo data restored* com *− Sales › Invoices: Credit note*. A descrição também volta à do exemplo. |
