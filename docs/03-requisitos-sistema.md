# Especificação de Requisitos de Software

Este documento define os **Requisitos Funcionais (RF)**, **Requisitos Não-Funcionais (RNF)** e as **Regras de Negócio (RN)** do projeto **Organizador de Imagens**, estabelecendo o escopo completo das aplicações Cliente Desktop (PyQt6) e Servidor Backend (Flask).

---

## 1. Visão Geral do Escopo

O **Organizador de Imagens** é um sistema distribuído composto por:
- **Cliente Desktop (PyQt6)**: Interface gráfica com recursos completos de catálogo (CRUD), visualização de miniaturas em tempo de execução, exportação de arquivos, inspeção de metadados e estatísticas de economia de memória via padrões de projeto (**Abstract Factory**, **Flyweight** e **Strategy**).
- **Servidor Backend (Flask)**: API RESTful responsável pelo armazenamento centralizado de metadados e arquivos de imagens binárias.
- **Modo Desconectado (Offline First)**: O cliente mantém integridade operacional e persistência em arquivo JSON local mesmo quando o backend remoto estiver indisponível.

---

## 2. Requisitos Funcionais (RF)

| ID | Nome do Requisito | Descrição Detalhada | Prioridade (MoSCoW) | Camada Responsável |
|---|---|---|---|---|
| **RF01** | **Importação de Imagens Locais** | O sistema deve permitir ao usuário selecionar um arquivo no sistema operacional por meio de diálogo de arquivo nativo e adicioná-lo ao catálogo. | Must Have | Cliente (UI / Service) |
| **RF02** | **Validação e Filtragem de Formatos** | O sistema deve validar a integridade e a extensão do arquivo no momento da importação, aceitando apenas formatos homologados (JPEG, PNG e BMP) e rejeitando extensões desconhecidas, diretórios ou arquivos corrompidos. | Must Have | Cliente (Abstract Factory) |
| **RF03** | **Extração de Metadados Técnicos** | O sistema deve inspecionar o arquivo selecionado e extrair largura, altura (em pixels), tamanho em disco (em bytes/KB), formato real e presença de canal alfa. | Must Have | Cliente (ImageReader) |
| **RF04** | **Listagem de Catálogo em Tempo Real** | A interface gráfica deve apresentar a listagem de todas as imagens cadastradas exibindo título e indicador de formato, com atualização imediata após qualquer operação. | Must Have | Cliente (MainWindow) |
| **RF05** | **Visualização de Detalhes e Painel Técnico** | Ao selecionar uma imagem da lista, a interface deve exibir sua miniatura gráfica, formato, resolução (LxA) e tamanho em disco formatado. | Must Have | Cliente (UI) |
| **RF06** | **Edição de Título da Imagem** | O usuário deve poder alterar o nome/título da imagem selecionada e salvar a alteração no catálogo local (e sincronizar na API caso online). | Must Have | Cliente (ImageService) |
| **RF07** | **Exclusão de Imagem com Confirmação** | O sistema deve permitir a remoção de uma imagem do catálogo mediante diálogo de confirmação do usuário (Yes/No), removendo-a da interface e do armazenamento. | Must Have | Cliente (ImageService) |
| **RF08** | **Exportação de Cópia da Imagem** | O usuário deve poder exportar uma cópia do arquivo de imagem para qualquer diretório do computador, mesmo que o arquivo local original tenha sido movido (baixando do servidor se necessário). | Should Have | Cliente / Servidor |
| **RF09** | **Alternância Dinâmica de Algoritmo de Miniatura** | O usuário deve poder alternar entre o modo de alta qualidade ("Smooth", antialiased) e o modo rápido ("Fast", nearest-neighbor), refletindo instantaneamente na miniatura exibida. | Must Have | Cliente (Strategy) |
| **RF10** | **Compartilhamento de Metadados de Formato em Memória** | O sistema deve compartilhar dados intrínsecos de formato entre todos os itens cadastrados por meio de um pool de Flyweights, exibindo em tempo real o total de instâncias economizadas. | Must Have | Cliente (Flyweight) |
| **RF11** | **Carga em Lote de Exemplos** | O sistema deve fornecer um botão para carregar em lote as imagens válidas presentes na pasta `sample_images/`, ignorando automaticamente arquivos de texto ou imagens corrompidas. | Could Have | Cliente (MainWindow) |
| **RF12** | **Persistência Local do Catálogo** | O cliente deve persistir o catálogo de imagens em arquivo JSON (`data/catalog.json`) a cada inclusão, edição ou exclusão, e restaurá-lo na inicialização. | Must Have | Cliente (ImageService) |
| **RF13** | **Monitoramento de Conectividade da API** | O cliente deve consultar o endpoint `/api/health` do servidor para detectar status online/offline sem bloquear a experiência do usuário. | Should Have | Cliente (ImageApiClient) |
| **RF14** | **Sincronização Remota com a API** | Sempre que uma imagem for cadastrada, editada ou excluída no cliente e a API estiver online, o cliente deve replicar a operação no backend Flask via requisições HTTP REST. | Should Have | Cliente / Servidor |
| **RF15** | **Download Remoto de Arquivo pelo Servidor** | O servidor deve disponibilizar endpoint para envio do binário da imagem como anexo de download (`/api/images/<id>/file`). | Should Have | Servidor (Flask) |

---

## 3. Requisitos Não-Funcionais (RNF)

| ID | Categoria | Descrição | Métrica / Critério de Aceitação |
|---|---|---|---|
| **RNF01** | **Arquitetura e Padrões GoF** | O software cliente deve implementar obrigatoriamente os três padrões de projeto exigidos: Abstract Factory (criacional), Flyweight (estrutural) e Strategy (comportamental). | Inspeção estática de código e conformidade com os módulos `client/patterns/`. |
| **RNF02** | **Desacoplamento e Modularidade** | As camadas de Interface Gráfica (`ui`), Modelos de Dados (`models`), Serviços (`services`) e Padrões de Projeto (`patterns`) devem residir em pacotes isolados. | Ausência de chamadas diretas de I/O na camada de interface gráfica (`MainWindow`). |
| **RNF03** | **Tolerância a Falhas e Resiliência** | A indisponibilidade total do servidor backend (porta 5000 fechada ou rede offline) não pode impedir nem interromper a execução do cliente desktop. | Execução sem exceções não tratadas ao realizar CRUD completo com o backend desligado. |
| **RNF04** | **Tempo de Resposta em Rede** | As chamadas de rede realizadas pelo cliente HTTP devem ter um tempo limite (*timeout*) estrito de no máximo 2,0 segundos para não congelar a interface síncrona. | Configuração explícita de `timeout=2.0` em todos os métodos de `ImageApiClient`. |
| **RNF05** | **Persistência Leve e Portabilidade** | O sistema não deve exigir instalação de SGBD relacional externo (MySQL, PostgreSQL, etc.), utilizando arquivos JSON estruturados para catálogo local e remoto. | Uso de `json.dump` / `json.load` nos caminhos `data/catalog.json` e `server/data/server_catalog.json`. |
| **RNF06** | **Segurança no Tratamento de Arquivos** | O servidor backend deve sanitizar nomes de arquivos recebidos contra ataques de injeção de caminho (*Path Traversal*) e colisões de nomes. | Aplicação de `werkzeug.utils.secure_filename` e prefixação com identificador UUID v4 exclusivo. |
| **RNF07** | **Compatibilidade de Plataforma** | O sistema deve executar de maneira consistente em sistemas operacionais modernos (Windows 10/11, Linux Ubuntu/Debian e macOS). | Código em Python 3.10+ sem dependências exclusivas de plataforma além das bibliotecas padrão e PyQt6/Pillow/Flask. |
| **RNF08** | **Eficiência de Memória** | As miniaturas geradas devem ser mantidas em cache no objeto `ImageItem` e invalidadas apenas na troca de estratégia de renderização ou alteração da imagem. | Nenhuma releitura física de disco ao alternar seleções na lista de imagens. |

---

## 4. Regras de Negócio (RN)

- **RN01 (Formatos Válidos)**: Apenas extensões `.jpg`, `.jpeg`, `.jpe`, `.jfif`, `.png`, `.bmp` e `.dib` são aceitas. Qualquer outra extensão deve disparar `UnsupportedFormatException`.
- **RN02 (Validação de Integridade do Binário)**: A extensão por si só não basta; o arquivo deve ser lido e verificado via `PIL.Image.verify()`. Arquivos com cabeçalho inválido ou corrompidos disparam `InvalidImageFileException`.
- **RN03 (Título Padrão)**: Caso o usuário não especifique um título na importação, o sistema assume automaticamente o nome do arquivo sem a extensão.
- **RN04 (Reversão de Título Vazio)**: Se o usuário tentar salvar um título em branco ou contendo apenas espaços, o sistema preserva o nome original do arquivo.
- **RN05 (Limpeza Física no Servidor)**: Ao excluir uma imagem no backend, o servidor remove a entrada do `server_catalog.json` e apaga fisicamente o arquivo correspondente da pasta `server/uploads/`.
- **RN06 (Imutabilidade do Estado Flyweight)**: Os objetos `ImageFormatFlyweight` são congelados (`frozen=True`) e compartilhados globalmente através da instância singleton de `FormatFlyweightFactory`.
