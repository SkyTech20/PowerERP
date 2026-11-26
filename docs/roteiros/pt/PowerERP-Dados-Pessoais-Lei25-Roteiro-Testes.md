# PowerERP — Dados pessoais (Lei 25 do Quebec): roteiro de testes

> **Atenção:** este roteiro foi escrito para o cenário *Pastry shop*, que foi removido (o padrão agora é *Maple products*, veja PowerERP-Demo-Bordo-Roteiro-Testes.md). Ele será refeito com os produtos de bordo; até lá, os códigos e números citados aqui não existem no demo.

Roteiro para testar a tela **Administration > Personal data** (item 9 do comparativo SCOR / ISO: pacote Lei 25). A tela acha o que o ERP guarda sobre uma pessoa, exporta o dossiê para entregar a ela, anonimiza a pessoa e guarda a política de privacidade (responsável, hospedagem, prazo de retenção). Só o perfil administrador vê a tela. Os rótulos estão em inglês, como aparecem no ERP com o botão **EN**.

**Antes de começar:** entre como administrador, vá em **Administration > System settings**, escolha o cenário **Pastry shop** e restaure os dados de demo.

---

## 1. Preparar uma pessoa

| Passo | Esperado |
|---|---|
| **Administration > Users**, **New**: *User name* `jtest`, *Name* `Julie Test`, *E-mail* `julie.test@patisserie.example`, *Role* PRODUCTION, uma senha; **Save** | Usuário criado. |
| Em outra janela anônima, entrar como `jtest`; **Production > Production orders**, **New**: DOUGH, 10 KG, *Start* hoje, *Due* amanhã, **Save**, **Release**; sair | Uma ordem criada e lançada por `jtest`. |

## 2. Achar a pessoa e abrir o dossiê

**Administration > Personal data** (item novo no menu **Administration**, entre *Audit log* e *Taxes*)

| Passo | Esperado |
|---|---|
| Abrir a tela | Três cartões: *Find a person*, *Retention*, *Privacy policy*. |
| Digitar `t` | Nada: são precisos 2 caracteres. |
| Digitar `test` | A linha *Julie Test*, tipo *User*, *Where* `jtest`, o e-mail, status *Active*. |
| Digitar `tremblay` | Julie Tremblay aparece como *Customer contact* e como *Ship-to contact* de CAFE-PLATEAU, com e-mail e telefone. |
| Voltar a `test` e **Open the file** de Julie Test | Cartão *File of Julie Test*: *What the ERP keeps* (nome, usuário, e-mail, perfil, idioma, ativo, criado, último login); *Where the user name is written*: *Production orders: created by* 1 e *released by* 1 com o número da ordem; *Audit log*: os eventos (criação pelo admin, login, criar, lançar) com o IP. |
| Botão **Anonymize…** | Desabilitado, com o aviso "This user is active. Deactivate the user in Administration > Users first." |

## 3. Exportar (direito de acesso e portabilidade)

| Passo | Esperado |
|---|---|
| **Export to Excel** | Baixa `personal-data-user-<id>.xlsx` com 3 abas: *Person*, *Documents*, *Audit log* (todos os eventos). Em FR as abas vêm em francês. |
| **Export (JSON)** | Baixa `personal-data-user-<id>.json`: `person`, `documents`, `auditLog`, `policy` (o responsável e a hospedagem). |

## 4. Anonimizar um usuário

| Passo | Esperado |
|---|---|
| **Administration > Users**, abrir `jtest`, desmarcar *Active*, **Save** | Usuário inativo. |
| Voltar a **Personal data**, achar `test`, **Open the file** | **Anonymize…** habilitado. |
| **Anonymize…**, confirmar | Mensagem "Anonymized (N records changed)". A busca `test` não acha mais ninguém. |
| **Administration > Users** | O usuário virou `anon-<id>`, nome *Anonymized*, sem e-mail, inativo. |
| **Production > Production orders**, a ordem do passo 1 | *Released by* mostra `anon-<id>`; a ordem continua igual. |
| **Administration > Audit log**, filtro de texto `jtest` | Nenhum evento. Os eventos de `anon-<id>` estão sem IP. Um evento novo *Anonymize* do admin, tela *Personal data*, ficha `user/<id>`. |
| Tentar entrar como `jtest` | Recusado. |
| Tentar anonimizar o próprio admin | Botão desabilitado (usuário ativo); pela API o erro é `cannot_anonymize_self` ou `user_active`. |

## 5. Anonimizar um contato

| Passo | Esperado |
|---|---|
| Buscar `tremblay`, **Open the file** do *Customer contact* | *What the ERP keeps*: nome, título, telefone, e-mail, cliente CAFE-PLATEAU. Texto "A contact is kept only on the customer…". |
| **Anonymize…**, confirmar | O contato some de **Sales > Customers > CAFE-PLATEAU**, aba de contatos. |
| *Ship-to contact* de Julie Tremblay, **Anonymize…** | No endereço de entrega CAFE do cliente, *Contact* e *Phone* ficam vazios; o endereço continua. |
| **Administration > Audit log**, texto `cafeduplateau` | Nenhum evento com o e-mail do contato. |

## 6. Ex-usuário

| Passo | Esperado |
|---|---|
| Criar o usuário `jold` e entrar com ele uma vez; como admin, **Administration > Users**, apagar `jold` | Usuário apagado. |
| **Personal data**, buscar `jold` | Linha tipo *Former user*: o nome ainda está no log de auditoria. |
| **Open the file**, **Anonymize…** | O nome `jold` some do log de auditoria (inclusive da ação de anonimizar). |

## 7. Política de privacidade e retenção

| Passo | Esperado |
|---|---|
| *Privacy policy*: *Person in charge* `Mohamed`, *Title* `President`, *E-mail* `privacy@patisserie.example`, *Hosted by* `Amazon Web Services`, *Hosting region* `ca-central-1 (Montreal)`, *Retention (months)* 24; **Save** | "Privacy policy saved." Reabrir a tela: os valores ficaram. |
| *E-mail* `nope`, **Save** | Erro de e-mail inválido; o campo recebe o foco. |
| *Retention (months)* 0, **Save** | Erro "Value out of range". |
| Cartão *Retention* | "Kept longer than the retention rule (24 months, before <data>)". Com o demo: "Nobody is kept longer than the retention rule." |
| **Sales > Customers**, desativar UNI-CAFE (sem fatura postada) | Voltando à tela, o contato de UNI-CAFE aparece em *Retention* com "No recent invoice". |
| **Anonymize the 1 persons…**, confirmar | "1 persons anonymized."; a lista fica vazia e o contato some do cliente. |

## 8. Acesso

| Passo | Esperado |
|---|---|
| Entrar com um usuário de perfil SALES ou PRODUCTION | O item **Personal data** não aparece; `#/admin/privacy` volta ao painel; a API responde 403. |
| **?** na tela | Abre a ajuda *Personal data*; cada campo da política tem seu ⓘ. |
