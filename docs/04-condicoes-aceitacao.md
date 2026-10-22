# Condições de Aceitação (Critérios de Aceite - BDD)

Este documento especifica as **Condições de Aceitação (Critérios de Aceite)** do sistema **Organizador de Imagens**, estruturadas formalmente segundo a metodologia **BDD (Behavior-Driven Development)** utilizando a sintaxe **Gherkin** (*Dado que... Quando... Então...*).

A validação cobre os fluxos do Cliente Desktop (PyQt6), as operações da API do Servidor Flask e o comportamento em condições anormais (falhas de conexão e arquivos corrompidos).

---

## 1. Metodologia de Validação

Cada critério de aceitação está mapeado diretamente a um ou mais **Requisitos Funcionais (RF)** ou **Requisitos Não-Funcionais (RNF)**, garantindo 100% de cobertura de rastreabilidade.

Os cenários são classificados em:
- **Caminho Feliz (Happy Path)**: Comportamento esperado em condições normais de uso.
- **Tratamento de Exceções e Casos de Borda (Edge Cases)**: Rejeição de arquivos inválidos, falhas de conectividade e persistência de integridade.

---

## 2. Cenários de Aceitação do Cliente Desktop

### CA01 — Importação com Sucesso de Imagem Suportada (JPEG, PNG, BMP)
- **Requisitos Vinculados**: RF01, RF02, RF03, RF04
- **Tipo**: Caminho Feliz
- **Cenário**: O usuário importa uma imagem válida compatível com as fábricas registradas.
  - **Dado que** o cliente desktop está em execução e a tela principal está visível,
  - **Quando** o usuário clica em "Adicionar Imagem" e seleciona um arquivo válido com extensão `.jpg`, `.png` ou `.bmp`,
  - **Então** o sistema deve carregar o arquivo através da fábrica correspondente (`ImageFormatFactorySelector`),
  - **E** extrair corretamente largura, altura e tamanho em bytes,
  - **E** adicionar o novo item na lista principal com o título e formato correspondente,
  - **E** persistir o registro no arquivo `data/catalog.json`.

---

### CA02 — Rejeição de Arquivo com Extensão Não Suportada
- **Requisitos Vinculados**: RF02, RN01
- **Tipo**: Tratamento de Erro
- **Cenário**: Tentativa de importação de arquivo com formato não suportado (ex: `.txt`, `.pdf`, `.gif`).
  - **Dado que** o usuário aciona o diálogo de seleção de arquivo,
  - **Quando** seleciona um arquivo com extensão não homologada (ex: `document.txt`),
  - **Então** o seletor de fábricas deve lançar `UnsupportedFormatException`,
  - **E** a interface deve exibir uma caixa de mensagem (`QMessageBox.warning`) alertando que a extensão não é suportada,
  - **E** nenhum item deve ser inserido na lista ou no catálogo persistido.

---

### CA03 — Rejeição de Imagem Corrompida ou Binário Inválido
- **Requisitos Vinculados**: RF02, RN02
- **Tipo**: Tratamento de Erro
- **Cenário**: Tentativa de importação de arquivo com extensão de imagem, porém conteúdo truncado ou corrompido.
  - **Dado que** existe um arquivo denominado `corrupted_image.jpg` com dados inválidos no cabeçalho,
  - **Quando** o usuário tenta importá-lo no cliente,
  - **Então** o método `ImageReader.read` deve executar `PIL.Image.verify()` e capturar a anomalia,
  - **E** disparar a exceção `InvalidImageFileException`,
  - **E** o cliente deve apresentar mensagem amigável de erro sem abortar a aplicação.

---

### CA04 — Rejeição de Seleção de Pasta / Diretório
- **Requisitos Vinculados**: RF02
- **Tipo**: Tratamento de Erro
- **Cenário**: Caminho informado aponta para uma pasta em vez de um arquivo.
  - **Dado que** um caminho de diretório seja passado para `import_image`,
  - **Quando** a rotina de validação verifica `os.path.isdir(file_path)`,
  - **Então** a operação deve disparar `InvalidImageFileException` informando que o caminho é uma pasta,
  - **E** a listagem de imagens não deve ser modificada.

---

### CA05 — Visualização de Detalhes e Troca de Seleção
- **Requisitos Vinculados**: RF04, RF05
- **Tipo**: Caminho Feliz
- **Cenário**: Seleção de item cadastrado para inspeção visual e técnica.
  - **Dado que** o catálogo possui ao menos uma imagem cadastrada,
  - **Quando** o usuário clica sobre uma imagem na lista (`QListWidget`),
  - **Então** o painel direito deve exibir a miniatura gráfica redimensionada da imagem,
  - **E** apresentar os rótulos de Formato (com MIME type), Dimensões (LxA px) e Tamanho em KB,
  - **E** preencher o campo editável com o título atual da imagem,
  - **E** habilitar os botões "Excluir Imagem", "Exportar Cópia" e "Salvar Nome".

---

### CA06 — Edição e Persistência do Título da Imagem
- **Requisitos Vinculados**: RF06, RN03, RN04
- **Tipo**: Caminho Feliz
- **Cenário**: Alteração bem-sucedida do título de uma imagem cadastrada.
  - **Dado que** uma imagem está selecionada na interface,
  - **Quando** o usuário digita um novo nome no campo "Nome" e clica em "Salvar Nome",
  - **Então** o sistema deve atualizar o atributo `title` do objeto `ImageItem`,
  - **E** regravar o catálogo local em `data/catalog.json`,
  - **E** atualizar o texto correspondente na lista principal imediatamente,
  - **E** sincronizar o novo título com o backend via `PUT /api/images/<id>` se o servidor estiver online.

---

### CA07 — Exclusão de Imagem Confirmada pelo Usuário
- **Requisitos Vinculados**: RF07, RN05
- **Tipo**: Caminho Feliz
- **Cenário**: Exclusão de item com confirmação explícita.
  - **Dado que** uma imagem está selecionada na interface,
  - **Quando** o usuário clica em "Excluir Imagem" e confirma a caixa de diálogo clicando em "Yes",
  - **Então** o registro deve ser removido do catálogo em memória e do arquivo `data/catalog.json`,
  - **E** o item deve desaparecer imediatamente da listagem da tela,
  - **E** o painel de visualização e detalhes deve retornar ao estado vazio/padrão,
  - **E** o servidor backend deve receber uma requisição `DELETE /api/images/<id>` se estiver online.

---

### CA08 — Cancelamento da Exclusão de Imagem
- **Requisitos Vinculados**: RF07
- **Tipo**: Caso Alternativo
- **Cenário**: Usuário aciona a exclusão, mas desiste da ação.
  - **Dado que** o diálogo de confirmação de exclusão está sendo exibido,
  - **Quando** o usuário clica em "No",
  - **Então** nenhuma alteração deve ser feita no catálogo ou na interface,
  - **E** a imagem permanece selecionada normalmente.

---

### CA09 — Exportação de Cópia da Imagem
- **Requisitos Vinculados**: RF08
- **Tipo**: Caminho Feliz
- **Cenário**: O usuário salva uma cópia da imagem em outra pasta do sistema.
  - **Dado que** uma imagem válida está selecionada,
  - **Quando** o usuário clica em "Exportar Cópia", seleciona um caminho de destino e confirma,
  - **Então** o sistema deve copiar o arquivo binário para o destino escolhido através de `shutil.copy2`,
  - **E** exibir mensagem de sucesso confirmando o caminho do arquivo gravado.

---

### CA10 — Alternância Dinâmica de Estratégia de Renderização (Strategy)
- **Requisitos Vinculados**: RF09, RNF01, RNF08
- **Tipo**: Caminho Feliz
- **Cenário**: Mudança em tempo de execução do algoritmo de interpolação da miniatura.
  - **Dado que** uma imagem com detalhes de alta resolução está selecionada,
  - **Quando** o usuário altera a seleção no combobox de "Alta Qualidade (Smooth)" para "Rápida (Fast)",
  - **Então** o objeto `ImageItem` deve invalidar o cache da miniatura anterior,
  - **E** aplicar a estratégia concreta `FastThumbnailStrategy.render(...)`,
  - **E** atualizar a imagem exibida no componente `lbl_preview` sem modificar o arquivo original.

---

### CA11 — Eficiência de Memória e Monitoramento do Pool Flyweight
- **Requisitos Vinculados**: RF10, RNF01, RNF08
- **Tipo**: Caminho Feliz
- **Cenário**: Compartilhamento de metadados imutáveis entre múltiplas imagens do mesmo formato.
  - **Dado que** o usuário importa 10 imagens no formato JPEG e 5 imagens no formato PNG,
  - **Quando** o sistema instancia os objetos `ImageItem`,
  - **Então** o `FormatFlyweightFactory` deve fornecer apenas 1 instância de flyweight para o formato JPEG e 1 para PNG,
  - **E** o rótulo inferior da tela deve reportar que 13 instâncias foram economizadas na memória RAM.

---

### CA12 — Carga em Lote de Exemplos (`sample_images`)
- **Requisitos Vinculados**: RF11
- **Tipo**: Caminho Feliz
- **Cenário**: Carregamento automático de arquivos de demonstração.
  - **Dado que** o diretório `sample_images/` contém imagens válidas e arquivos inválidos (como `corrupted_image.jpg` e `document.txt`),
  - **Quando** o usuário clica no botão "Carregar Exemplos",
  - **Então** todas as imagens válidas (`city_night.jpg`, `sunset_landscape.jpg`, `graphic_shapes.png`, `tech_grid.png`) devem ser importadas,
  - **E** os arquivos inválidos devem ser descartados sem travar a aplicação,
  - **E** a lista deve ser atualizada com o lote de imagens carregadas.

---

### CA13 — Persistência e Restauração entre Sessões
- **Requisitos Vinculados**: RF12, RNF05
- **Tipo**: Caminho Feliz
- **Cenário**: Fechamento e reabertura da aplicação desktop.
  - **Dado que** existem imagens cadastradas na sessão atual,
  - **Quando** o usuário encerra o programa e o inicia novamente via `python main.py`,
  - **Então** a camada `ImageService` deve ler `data/catalog.json`,
  - **E** recriar os itens que continuem existindo no disco local,
  - **E** apresentar a lista com os mesmos títulos e dados da sessão anterior.

---

### CA14 — Resiliência Operacional com Servidor Offline (Offline First)
- **Requisitos Vinculados**: RF13, RNF03, RNF04
- **Tipo**: Resiliência / Falha de Rede
- **Cenário**: Uso da aplicação com o backend Flask desligado.
  - **Dado que** o servidor backend não está em execução na porta 5000,
  - **Quando** o usuário realiza operações de importação, edição de título e exclusão no cliente desktop,
  - **Então** o `ImageApiClient.check_health()` deve registrar status offline sem lançar erro não tratado para o usuário,
  - **E** todas as operações locais devem ser concluídas com sucesso,
  - **E** o cliente não deve travar nem ultrapassar o timeout de 2.0 segundos.

---

## 3. Cenários de Aceitação do Servidor Backend (API Flask)

### CA15 — Verificação de Saúde da API (`GET /api/health`)
- **Requisitos Vinculados**: RF13
- **Tipo**: Caminho Feliz
- **Cenário**: Cliente ou monitor consulta o estado do backend.
  - **Dado que** o servidor Flask está em execução (`python server/app.py`),
  - **Quando** uma requisição HTTP `GET` é enviada para `http://127.0.0.1:5000/api/health`,
  - **Então** o servidor deve responder com status HTTP `200 OK`,
  - **E** o corpo da resposta deve conter JSON com `status: "online"`, `total_images` e `timestamp`.

---

### CA16 — Listagem de Catálogo Remoto (`GET /api/images`)
- **Requisitos Vinculados**: RF14
- **Tipo**: Caminho Feliz
- **Cenário**: Consulta a todas as imagens cadastradas no backend.
  - **Dado que** o servidor possui imagens registradas em `server_catalog.json`,
  - **Quando** uma requisição HTTP `GET` é enviada para `/api/images`,
  - **Então** a resposta deve ter código HTTP `200 OK` e retornar um array JSON com todos os registros cadastrados.

---

### CA17 — Upload de Imagem com Sucesso (`POST /api/images`)
- **Requisitos Vinculados**: RF14, RNF06
- **Tipo**: Caminho Feliz
- **Cenário**: Envio de arquivo binário para o servidor.
  - **Dado que** o cliente envia uma requisição `POST` com cabeçalho `multipart/form-data` contendo o campo `file` e campo opcional `title`,
  - **Quando** o servidor recebe o payload,
  - **Então** deve sanitizar o nome via `secure_filename`,
  - **E** gerar um identificador UUIDv4 único,
  - **E** salvar o binário no diretório `server/uploads/`,
  - **E** persistir os metadados em `server_catalog.json`,
  - **E** responder com status HTTP `201 Created` e o objeto JSON da imagem cadastrada.

---

### CA18 — Rejeição de Upload sem Arquivo (`POST /api/images`)
- **Requisitos Vinculados**: RF14, RNF06
- **Tipo**: Tratamento de Erro
- **Cenário**: Requisição POST sem o campo multipart obrigatório.
  - **Dado que** uma requisição `POST /api/images` é feita sem o parâmetro `file`,
  - **Quando** o servidor processa a requisição,
  - **Então** deve abortar o processamento e responder com código HTTP `400 Bad Request`,
  - **E** retornar mensagem de erro descritiva `{"error": "Nenhum arquivo enviado"}`.

---

### CA19 — Atualização de Título no Servidor (`PUT /api/images/<id>`)
- **Requisitos Vinculados**: RF14
- **Tipo**: Caminho Feliz
- **Cenário**: Atualização de registro remoto por ID.
  - **Dado que** existe uma imagem cadastrada com determinado `image_id`,
  - **Quando** uma requisição `PUT /api/images/<image_id>` é enviada com payload JSON `{"title": "Foto das Ferias"}`,
  - **Então** o servidor deve alterar o atributo `title` do registro,
  - **E** atualizar o arquivo `server_catalog.json`,
  - **E** responder com HTTP `200 OK` contendo os dados atualizados.

---

### CA20 — Download de Arquivo de Imagem (`GET /api/images/<id>/file`)
- **Requisitos Vinculados**: RF15
- **Tipo**: Caminho Feliz
- **Cenário**: Obtenção do binário da imagem hospedada.
  - **Dado que** existe um arquivo associado ao `image_id` no diretório `uploads/`,
  - **Quando** é efetuada uma requisição `GET /api/images/<image_id>/file`,
  - **Então** o servidor deve responder com HTTP `200 OK`,
  - **E** transmitir o arquivo binário com cabeçalho `Content-Disposition: attachment` e o nome original de download.

---

### CA21 — Consulta ou Acesso a ID Inexistente na API
- **Requisitos Vinculados**: RF14, RF15
- **Tipo**: Tratamento de Erro
- **Cenário**: Requisição para imagem não existente.
  - **Dado que** é feita uma requisição `GET`, `PUT`, `DELETE` ou `GET /file` para um UUID inexistente,
  - **Quando** o servidor busca a chave no catálogo,
  - **Então** deve responder com status HTTP `404 Not Found` e corpo `{"error": "Imagem nao encontrada"}`.

---

## 4. Matriz de Rastreabilidade (Requisitos x Critérios de Aceitação)

| Requisito | Critérios de Aceitação Correspondentes |
|---|---|
| **RF01 (Importação)** | CA01 |
| **RF02 (Validação Formatos)** | CA01, CA02, CA03, CA04 |
| **RF03 (Extração Metadados)** | CA01, CA05 |
| **RF04 (Listagem)** | CA01, CA05, CA07, CA12, CA13 |
| **RF05 (Visualização/Detalhes)**| CA05, CA10 |
| **RF06 (Edição Título)** | CA06, CA19 |
| **RF07 (Exclusão)** | CA07, CA08 |
| **RF08 (Exportação)** | CA09 |
| **RF09 (Strategy Miniatura)** | CA10 |
| **RF10 (Flyweight Formatos)** | CA11 |
| **RF11 (Carga Exemplos)** | CA12 |
| **RF12 (Persistência Local)** | CA01, CA06, CA07, CA13 |
| **RF13 (Conectividade API)** | CA14, CA15 |
| **RF14 (CRUD Servidor)** | CA16, CA17, CA18, CA19, CA21 |
| **RF15 (Download Servidor)** | CA20, CA21 |
| **RNF01 a RNF08** | CA01, CA03, CA10, CA11, CA14, CA17 |
