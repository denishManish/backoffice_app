## Оглавление

- [Описание работы Backend'а](#описание-работы-backenda)
    - [Описание работы в локальном окружении](#описание-работы-в-локальном-окружении)
    - [Описание работы в production окружении](#описание-работы-в-production-окружении)
- [Размещение на новой машине в локальном окружении](#размещение-на-новой-машине-в-локальном-окружении)
- [Размещение на новой машине в production окружении](#размещение-на-новой-машине-в-production-окружении)
- [Deploy в production](#deploy-в-production)
- [Документация](#документация)
- [Наборы команд для управления и работы с Docker Compose](#наборы-команд-для-управления-и-работы-с-docker-compose)
    - [Заметки по Docker Compose](#заметки-по-docker-compose)
    - [Запуск](#запуск)
    - [Проверка статуса контейнеров](#проверка-статуса-контейнеров)
    - [Перезапуск](#перезапуск)
    - [Выполнение команд в контейнере](#выполнение-команд-в-контейнере)
    - [Логи из контейнера](#логи-из-контейнера)


## Описание работы Backend'а

Работа Backend'а осуществляется с помощью Docker Compose. Каждый сервис контейнизируется и помещается в изолированное пространство. 

Имеются следующие сервисы: 
- django
- postgres
- minio
- minio-setup (только создает bucket)
- nginx

Docker Compose для своей работы использует конфигурационный файл _compose.yml_. В нем описываются вышеупомянутые сервисы, их параметры, а также объявляются томы (volumes), способ хранения данных вне контейнеров на локальной машине, что позволяет противостоять побочному эффекту изолированности контейнеров - потере данных при удалении контейнера. Благодаря томам локальные директории связываются с директориями внутри контейнеров, данный механизм можно сравнить с мягкими ссылками в Linux. 

Backend в Gitlab репозитории подготовлен для легкого размещения как в локальном, так и в production окружении. 


### Описание работы в локальном окружении

Для локальной разработки backend уже настроен и особых дополнительных действий не требует. Docker Compose, используя готовые файлы _compose.yml_, _.env_, _nginx/local.conf_, способен запустить весь backend. 

После запуска при изменениях в коде сервер подвергается __hot reload__.

[Инструкция по размещению](#размещение-на-новой-машине-в-локальном-окружении)


### Описание работы в production окружении

Для работы в production окружении применяются файлы:

<details><summary> compose.yml, compose.override.yml </summary>

При запуске backend'а Docker Compose применяет _compose.yml_ и, если имеется, _compose.override.yml_ для дополнения и перезаписывания совпадающих мест _compose.yml_.

Файл _compose.override.yml_ переопределяет:
- какой env файл использовать (_prod.env_)
- определяет использование gunicorn для django (`command: gunicorn -c gunicorn.conf.py`)
- с помощью томов (volumes):
    - добавляет сертификаты для HTTPS в контейнеры minio, nginx
    - выводит логи из контейнера на локальную машину (пример - `./logs/nginx:/var/log/nginx`)
    - переопределяет конфигурационный файл для nginx (`./nginx/prod.conf:/etc/nginx/conf.d/default.conf`)

Подробнее можно изучить в *_compose.override.yml*.

Файл *_compose.override.yml* игнорируется Docker Compose из-за имени. Таким образом, при локальном окружении он не используется, а при production окружении используется для создания _compose.override.yml_. <br> 
Для того, чтобы Git не воспринимал изменения при данных действиях, _compose.override.yml_ не просто переименовывается из *_compose.override.yml*, а именно копируется из него. Также ради этого _compose.override.yml_ добавлен в _.gitignore_. <br>
По сути *_compose.override.yml* был добавлен в репозиторий для использования как готовый шаблон.
</details>


<details><summary> .env, prod.env </summary>

Docker Compose не способен загрузить env файл с нестандартным названием до билда, только стандартный _.env_. Из-за этого необходимо использование двух файлов.

Сначала Docker Compose загружает файл с названием _.env_ из той же директории (поведение по умолчанию для Docker Compose), затем, так как _compose.override.yml_ переопределяет сервисы на использование _prod.env_, загруженные переменные __перезаписываются__ значениями из _prod.env_. 

Если в _prod.env_ будут добавлены переменные, использующиеся Docker Compose при запуске контейнеров, необходимо добавить эти переменные также в _.env_.

Уточнения для некоторых переменных:

- `POSTGRES_HOST` должно быть значение хоста для базы данных. Так как Postgres размещается на той же машине в контейнере, задается название сервиса _postgres_. Если база данных будет размещаться на другом хосте, необходимо изменить данное значение соответственно. <br>
- `SECRET_KEY` используется для создания hash-паролей для пользователей. Он должен быть сгенерирован отдельно.
- `MINIO_SERVER_URL` должен быть адрес для сервиса MinIO. 
</details>

<details><summary> gunicorn.conf.py </summary>

В production окружении используется Python WSGI Gunicorn. Для его работы применяется конфигурационный файл, определяющий:
- число workers
- типа workers (используется _gthread_ - потоковый worker)
- число потоков
- путь для логов 

Для повышения скорости обработки запросов можно увеличить число workers, но рекомендуется число не больше `(2 x $num_cores) + 1`, где num_cores - число ядер машины.
</details>

<details><summary>nginx/prod.conf</summary>

Nginx настроен на HTTPS по домену. Сертификаты получены благодаря _letsencrypt_ с помощью _certbot_ и действительны 90 дней. _Certbot_ устанавливает автоматическое обновление сертификатов. Так как _certbot_ поднимает временный сервер для обновления сертификатов, необходимо преждевременно освободить порт 80 и перезапустить сервисы, использующие сертификаты (_nginx_ и _minio_). Для автоматизации были созданы два скрипта (_certbot_ при обновлении сертификатов исполняет все скрипты из _renewal-hooks/_):

- _stop.sh_ останавливает контейнер _nginx_ для освобождения порта 80. <br> Расположен в _/etc/letsencrypt/renewal-hooks/pre_, скрипты откуда выполняются до процесса обновления сертификатов.
- _restart.sh_ перезапускает контейнеры _nginx_, _minio_ после обновления сертификатов. <br> Расположен в _/etc/letsencrypt/renewal-hooks/deploy_, скрипты откуда выполняются после процесса обновления сертификатов.

Прописаны пути внутри контейнера для логов:

- access_log - обычные логи о поступающих на Nginx запросах
- error_log - логи для ошибок и предупреждений Nginx
</details>

В production окружении при изменениях в коде сервер необходимо [перезапустить](#перезапуск).

<details><summary>blacklist app</summary>

В Django было добавлено _blacklist app_, чтобы при неправомерных или подозрительных действиях пользователя закрыть ему доступ к ресурсу, поместив refresh токен в черный список и тем самым прекрать возможность обновления access токена. <br>
Это возможно сделать в панели администратора по пути `/admin`.

Если потребности в данном функционале не имеется, его возможно убрать в _BackofficeApp/BackofficeApp/settings.py_ и затем перезапустить сервис _django_, если он был запущен.
```
...
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt.token_blacklist',  # удалить или закомментировать данную строку
    ...
]
...

# перезапустить django, если был запущен
docker compose restart django
```
</details>

[Инструкция по размещению](#размещение-на-новой-машине-в-production-окружении)


## Размещение на новой машине в локальном окружении

- установка Docker, Docker Compose (ubuntu - https://docs.docker.com/engine/install/ubuntu/)
- (опционально) добавить пользователя в группу __docker__ для использования команд Docker без __sudo__
    ```
    # Если группы нет в системе
    sudo groupadd docker

    # Добавляем в группу себя и применяем изменения без перезахода
    sudo usermod -aG docker $USER
    newgrp docker

    # Проверяем
    docker ps
    ```
- загружаем backend из репозитория
    ```
    # клонирование репозиторий и переход в ветку development
    git clone https://gitlab.com/proginart/backend

    # загрузка последних изменений (через какое-то время, если были новые коммиты)
    git pull origin main
    ```
- запускаем backend
    ```
    docker compose build
    docker compose up -d  # detached, запустить на фоне

    # альтернатива:
    # обычный запуск с логами, захватывающими терминал 
    docker compose up   
    ```
    Для локального окружения из-за отсутствия логов в файлах предпочтительнее использовать `docker compose up`, так как в терминале будут выводиться логи контейнеров о успешности запуска. Если нет желания блокировать терминал логами или открытия нового терминала, возможно запуска в detach режиме и [проверить логи из контейнеров по отдельности](#логи-из-контейнера). 
    
- загрузка mockdata
    ```
    docker compose exec django sh -c "cd BackofficeApp && python manage.py setup_project" 
    ```
    Конкретнее о загружаемых данных в _BackofficeApp/user_management/management/commands/setup_project.py_, а также _BackofficeApp/user_management/fixtures_


### Размещение на новой машине в production окружении 

- установка Docker, Docker Compose (ubuntu - https://docs.docker.com/engine/install/ubuntu/)
- добавить пользователя в группу __docker__ для использования команд Docker без __sudo__
    ```
    # Если группы нет в системе
    sudo groupadd docker

    # Добавляем в группу себя и применяем изменения без перезахода
    sudo usermod -aG docker $USER
    newgrp docker

    # Проверяем
    docker ps
    ```
    Обязательный пункт в отличии от локального окружения, так как будут использоваться скрипты, которым необходимо исполнять команды `docker compose` без __sudo__.

- загружаем backend из репозитория
    ```
    cd /srv/

    # клонирование репозиторий и переход в ветку development
    git clone https://gitlab.com/repo/backend

    # загрузка последних изменений (через какое-то время, если были новые коммиты)
    git pull origin main
    ```

- создать _prod.env_

    - создать копию _.env_ файла -> _prod.env_ <br> 
        ```
        cp .env prod.env
        ```
    - сгенерировать секретный ключ для `SECRET_KEY` в _prod.env_
        ```
        # временно запускаем контейнеры
        docker compose build
        docker compose up -d

        # генерируем секретный ключ
        docker compose exec django python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

        # останавливаем и удаляем контейнеры
        docker compose down
        ```
    - в _prod.env_ установить `SECRET_KEY=`*сгенерированный ключ из предыдущего шага*
    - в _prod.env_ установить `DJANGO_DEBUG=False`
    - в _prod.env_ MINIO_SERVER_URL

- получить сертификаты для HTTPS с помощью _letsencrypt_ и _certbot_
    - установка
        ```
        sudo apt update
        sudo apt install certbot python3-certbot-nginx
        ```

    - получение сертификатов для домена <br>
        (порт 80 должен быть свободен) 
        ```
        sudo certbot certonly --standalone -d <domain>
        ```

    - автоматизация обновления сертификатов
        - Скопировать скрипт _stop.sh_ в _/etc/letsencrypt/renewal-hooks/pre_
            ```
            chmod +x ./stop.sh
            sudo cp ./stop.sh /etc/letsencrypt/renewal-hooks/pre
            ```
        - Скопировать скрипт _restart.sh_ в _/etc/letsencrypt/renewal-hooks/deploy_
            ```
            chmod +x ./restart.sh
            sudo cp ./restart.sh /etc/letsencrypt/renewal-hooks/deploy
            ```

        Проверить статус, получить общую информацию можно по команде
        ```
        sudo certbot certificates
        ```
    
    - для ручной проверки получения сертификатов можно вызвать следующую команду, симулирующую процесс обновления сертификатов <br>
        (порт 80 должен быть свободен) 
        ```
        sudo certbot renew --dry-run
        ```

- создать копию *_compose.override.yml* -> _compose.override.yml_ <br> 
    ```
    cp _compose.override.yml compose.override.yml
    ```

- установить cron routine для ежедневного удаления истекших refresh токенов из _outstanding list_ и _blacklist_ приложения _simple jwt blacklist app_ 
    ```
    chmod +x delete_expired.sh

    crontab -e

    # внутри файла вставить следующее
    0 3 * * * /srv/backend/delete_expired.sh   # выполнять скрипт в 3 ночи каждый день

    # проверка установки cron routine
    crontab -l
    ```

- запускаем backend
    ```
    docker compose build
    docker compose up -d  # detached, запустить на фоне

    # альтернатива:
    # обычный запуск с логами, захватывающими терминал 
    docker compose up   
    ```

- загрузка разрешений для ролей/групп
    ```
    docker compose exec django sh -c "cd BackofficeApp && python manage.py fill_groups" 
    ```
    Конкретнее о разрешениях для каждой роли/группы в `BackofficeApp/user_management/management/commands/fill_groups.py`



## Deploy в production

Закрытие Browsable API:

- в _BackofficeApp/BackofficeApp/urls.py_:
    ```
    ...
    urlpatterns = (
        ...
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),   # удалить или закомментировать
        ...
    )
    ```

- в _BackofficeApp/BackofficeApp/settings.py_:
    ```
    REST_FRAMEWORK = {
        ...
        'DEFAULT_AUTHENTICATION_CLASSES': [
            ...
            'rest_framework.authentication.SessionAuthentication',   # удалить или закомментировать
        ],
        ...
        'DEFAULT_RENDERER_CLASSES': (
            ...
            'rest_framework.renderers.BrowsableAPIRenderer',         # удалить или закомментировать
        ),
    }
    ```


После загрузки билда frontend'а поменять следующее:

- в _BackofficeApp/user_management/views.py_:
    ```
    class CustomTokenObtainPairView(TokenObtainPairView):
        ...
        def post(self, request, *args, **kwargs):
            ...
            response.set_cookie(
                key='access_token',
                ...
                samesite='None',   # изменить на 'Strict' 
                ...
            )
            response.set_cookie(
                key='refresh_token',
                ...
                samesite='None',   # изменить на 'Strict' 
                ...
            )
    
    class CustomTokenRefreshView(TokenRefreshView):
        def post(self, request, *args, **kwargs):
            ...
            response.set_cookie(
                key='refresh_token',
                ...
                samesite='None',   # изменить на 'Strict'
                ...
            )
    ```

- в _BackofficeApp/BackofficeApp/settings.py_:
    ```
    CORS_ALLOWED_ORIGINS = [
        ...
        "http://localhost:5173",           # удалить или закомментировать адрес для локального frondend'а
    ]
    ```

## Документация

Документация создается с помощью _mkdocs_ по большей части на основе docstrings классов и функций. Если внесены изменения в код, то следует обновить docstring соответствующего класса или функции. 

Сами файлы-страницы документации для генерирования расположены в _docs/md_. При добавлении новых файлов необходимо добавить их в _index.md_ (начальная страница) и в _mkdock.yml_ в _nav_ (навигационная панель).

Отдельно следует упомянуть файл _api.md_, описывающий API. Его содержимое необходимо обновлять именно в самом файле Markdown.

Стиль и другие настройки определяет конфигурационный файл _mkdock.yml_.


## Наборы команд для управления и работы с Docker Compose

### Заметки по Docker Compose

> На Linux команды `docker compose`, на Windows `docker-compose`

> Все команды `docker compose` выполняются из директории с файлом _compose.yml_


### Запуск
```
docker compose build
docker compose up -d  # detached, запустить на фоне

# альтернатива:
# обычный запуск с логами, захватывающими терминал 
docker compose up   
``` 

### Проверка статуса контейнеров

Выводит действующие контейнеры, их названия, image, сервис, когда созданы, текущий статус со продолжительностью работы, порты
```
docker compose ps
```

### Перезапуск 

```
docker compose down
docker compose build
docker compose up -d
```

### Выполнение команд в контейнере

```
docker compose exec <service name from compose.yml> <command> 

# к примеру, заход в shell контейнера с django для исполнения некоторых команд
docker compose exec django sh
```

### Логи из контейнера

Полезны разве что в локальном окружении, так как в production логи записываются в файлы
```
docker compose logs <service name from compose.yml>
```