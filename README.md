# Organizador de Imagens (Projeto 10)

Disciplina: Paradigmas de Programação  
Turma: CC5AN  
Professor: Alex Carneiro  
Modulo: Cliente Desktop QT (PyQt6) e Servidor Flask (server/)

---

## 1. Visao Geral do Projeto

O Organizador de Imagens e uma aplicacao desktop desenvolvida em Python e PyQt6 com foco na demonstracao dos padroes de projeto solicitados (Abstract Factory, Flyweight e Strategy).

O sistema oferece um CRUD simples de imagens e metadados, suporte aos formatos JPEG, PNG e BMP, persistencia em formato JSON (sem banco de dados externo ou APIs de terceiros) e comunicacao desacoplada para o servidor Flask.

---

## 2. Design Patterns Implementados

### Criacional - Abstract Factory
Cria familias compativeis de leitores e geradores de miniaturas para os formatos suportados.
- Fabrica Abstrata: `ImageFormatFactory`
- Fabricas Concretas: `JPEGFormatFactory`, `PNGFormatFactory`, `BMPFormatFactory`
- Produtos Abstratos: `ImageReader` e `ThumbnailGenerator`
- Seletor de Fabrica: `ImageFormatFactorySelector`

```mermaid
classDiagram
    class ImageFormatFactory {
        <<interface>>
        +create_reader() ImageReader
        +create_thumbnail_generator() ThumbnailGenerator
        +format_name str
        +supported_extensions tuple
    }
    class JPEGFormatFactory {
        +create_reader() JPEGReader
        +create_thumbnail_generator() JPEGThumbnailGenerator
    }
    class PNGFormatFactory {
        +create_reader() PNGReader
        +create_thumbnail_generator() PNGThumbnailGenerator
    }
    class BMPFormatFactory {
        +create_reader() BMPReader
        +create_thumbnail_generator() BMPThumbnailGenerator
    }
    class ImageReader {
        <<interface>>
        +read(file_path) tuple
    }
    class ThumbnailGenerator {
        <<interface>>
        +generate_thumbnail(qimage, target_size, smooth) QPixmap
    }

    ImageFormatFactory <|.. JPEGFormatFactory
    ImageFormatFactory <|.. PNGFormatFactory
    ImageFormatFactory <|.. BMPFormatFactory
    ImageReader <|.. JPEGReader
    ImageReader <|.. PNGReader
    ImageReader <|.. BMPReader
    ThumbnailGenerator <|.. JPEGThumbnailGenerator
    ThumbnailGenerator <|.. PNGThumbnailGenerator
    ThumbnailGenerator <|.. BMPThumbnailGenerator
```

---

### Estrutural - Flyweight
Compartilha metadados e recursos comuns de cada formato entre as miniaturas para economia de memoria.
- Estado Intrinseco (`ImageFormatFlyweight`): formato, MIME type, suporte a canal alfa, cores e rotulo do badge.
- Estado Extrinseco (`ImageItem`): caminho, dimensoes, tamanho em bytes, titulo, tags, descricao.
- Fabrica Flyweight (`FormatFlyweightFactory`): mantem pool unico de formatos e metadados compartilhados.
- Observabilidade: comprovada via `FlyweightStatsWidget` e inspecao de enderecos de memoria.

```mermaid
classDiagram
    class ImageFormatFlyweight {
        +format_name: str
        +mime_type: str
        +supports_transparency: bool
        +badge_bg_color: str
        +badge_label: str
        +draw_badge(painter, rect)
        +get_summary_text(size, w, h)
    }

    class FormatFlyweightFactory {
        -_flyweights: dict
        -_served_requests: int
        +get_flyweight(format_name) ImageFormatFlyweight
        +get_pool_size() int
        +get_stats() dict
    }

    class ImageItem {
        +id: str
        +file_path: str
        +width: int
        +height: int
        +file_size_bytes: int
        +title: str
        +tags: list
        +flyweight: ImageFormatFlyweight
        +get_thumbnail(strategy, size)
    }

    FormatFlyweightFactory o-- ImageFormatFlyweight
    ImageItem --> ImageFormatFlyweight
```

---

### Comportamental - Strategy
Permite a troca de algoritmos de ordenacao e geracao de miniaturas.
- Estrategias de Ordenacao (`SortStrategy`):
  - `SortByNameAscStrategy` (Nome A-Z)
  - `SortByNameDescStrategy` (Nome Z-A)
  - `SortBySizeAscStrategy` (Tamanho menor primeiro)
  - `SortBySizeDescStrategy` (Tamanho maior primeiro)
- Estrategias de Miniatura (`ThumbnailRenderStrategy`):
  - `SmoothThumbnailStrategy` (Alta qualidade)
  - `FastThumbnailStrategy` (Rapida)

```mermaid
classDiagram
    class SortStrategy {
        <<interface>>
        +name: str
        +sort(items: list) list
    }
    class SortByNameAscStrategy {
        +sort(items: list) list
    }
    class SortByNameDescStrategy {
        +sort(items: list) list
    }
    class SortBySizeAscStrategy {
        +sort(items: list) list
    }
    class SortBySizeDescStrategy {
        +sort(items: list) list
    }

    SortStrategy <|.. SortByNameAscStrategy
    SortStrategy <|.. SortByNameDescStrategy
    SortStrategy <|.. SortBySizeAscStrategy
    SortStrategy <|.. SortBySizeDescStrategy
```

---

## 3. Diagrama de Classes do Cliente QT

```mermaid
classDiagram
    direction TB

    class MainWindow {
        -service: ImageService
        -selected_image_id: str
        -card_widgets: list
        +refresh_gallery()
        +_on_import_files()
        +_on_load_samples()
        +_on_sort_changed()
    }

    class ImageCard {
        +item: ImageItem
        +thumbnail_strategy: ThumbnailRenderStrategy
        +update_thumbnail(strategy)
        +clicked
        +double_clicked
    }

    class ImageDetailDialog {
        +item: ImageItem
        +service: ImageService
        +_on_save_metadata()
        +_on_export()
        +_on_delete()
    }

    class ImageService {
        -_items: dict
        -storage_path: str
        -api_client: ImageApiClient
        +import_image(file_path, title, desc, tags) ImageItem
        +get_all_images() list
        +get_sorted_images(sort_strat) list
        +update_image_metadata(id, title, desc, tags) ImageItem
        +delete_image(id) bool
        +export_image(id, dest_path) bool
        +get_flyweight_stats() dict
    }

    class ImageItem {
        +id: str
        +file_path: str
        +width: int
        +height: int
        +file_size_bytes: int
        +title: str
        +tags: list
        +flyweight: ImageFormatFlyweight
    }

    class ImageApiClient {
        +base_url: str
        +check_health() bool
        +list_images() list
        +upload_image(file_path, metadata) dict
        +update_metadata(id, metadata) dict
        +delete_image(id) bool
        +download_image(id, dest_path) bool
    }

    MainWindow --> ImageService
    MainWindow --> ImageCard
    MainWindow ..> ImageDetailDialog
    ImageCard --> ImageItem
    ImageDetailDialog --> ImageService
    ImageDetailDialog --> ImageItem
    ImageService --> ImageItem
    ImageService --> ImageApiClient
```

---

## 4. Requisitos do Sistema

### Requisitos Funcionais (RF)
- RF01 - Importar Imagem (Create): Selecao e cadastro de imagens locais nos formatos JPEG, PNG e BMP.
- RF02 - Visualizar Galeria (Read): Exibicao em grade com miniatura, dimensoes e tamanho.
- RF03 - Detalhes e Edicao (Update): Visualizacao da imagem e edicao de titulo, tags e descricao.
- RF04 - Exclusao (Delete): Remocao de imagem do catalogo com confirmacao.
- RF05 - Exportacao (Download): Salvar copia do arquivo no caminho escolhido pelo usuario.
- RF06 - Ordenacao (Strategy): Troca de ordenacao por Nome (A-Z / Z-A) ou Tamanho (crescente / decrescente).
- RF07 - Validacao de Arquivo: Rejeicao segura de arquivos corrompidos, formatos invalidos ou caminhos inexistentes.

### Requisitos Nao-Funcionais (RNF)
- RNF01 - Sem banco de dados externo ou APIs de terceiros (armazenamento JSON simples).
- RNF02 - Desacoplamento estrutural conforme padroes GoF (Abstract Factory, Flyweight, Strategy).
- RNF03 - Interface desktop desenvolvida em PyQt6.
- RNF04 - Testabilidade automatizada via pytest.

---

## 5. Cenarios de Teste

| Teste | Nome | Acao | Resultado Esperado | Status |
|---|---|---|---|---|
| T10.1 | Importar e visualizar imagens | Importar imagens PNG e JPEG validas | Imagens catalogadas, miniaturas exibidas, metadados persistidos | Aprovado |
| T10.2 | Arquivo invalido e caminho ausente | Tentar importar arquivo .txt, corrompido ou inexistente | Erro tratado graciosamente, sem travar o QT e sem gravar dados invalidos | Aprovado |
| T10.3 | Upload, metadados e download | Editar metadados e exportar copia da imagem | Metadados persistidos e copia exportada identica ao original | Aprovado |
| T10.4 | Flyweight e Strategy | Importar imagens e alternar ordenacao | Reuso de instancias Flyweight comprovado e lista reordenada via Strategy | Aprovado |

---

## 6. Instrucoes de Execucao

### Instalacao de dependencias
```bash
pip install -r requirements.txt
```

### Executar o Cliente QT
```bash
python main.py
```

### Executar os Testes Automatizados
```bash
pytest -v
```

### Executar o Servidor Flask (Opcional)
```bash
python server/app.py
```
