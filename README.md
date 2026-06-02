# Valorant team analytics

Python-пайплайн для анализа матчей небольшой Valorant-команды за выбранные акты. Он строит:

- число игр, победы и win rate каждой наблюдавшейся комбинации игроков;
- win rate каждого игрока на каждой роли;
- CSV-матрицу `игрок → роль` для матчей полным стаком из пяти отслеживаемых игроков;
- краткий Markdown-отчёт.

## Почему проект не обращается к Tracker.gg автоматически

У Tracker Network нет публичного Valorant API. Представители Tracker Network отдельно указывают, что внутренние Valorant endpoints использовать нельзя и что для Valorant нужно запрашивать доступ у Riot Games:

- [Valorant API Inquiry](https://feedback.tracker.gg/t/valorant-api-inquiry/28078/2)
- [Valorant rank API](https://feedback.tracker.gg/t/valorant-rank-api/25647/2)
- [Riot Developer Portal](https://developer.riotgames.com/)

Поэтому проект намеренно **не** обходит Cloudflare, не автоматизирует браузер и не вызывает внутренние endpoints Tracker.gg. Он принимает нормализованный JSON, полученный из разрешённого источника: собственного экспорта, вручную подготовленного файла или адаптера к API, доступ к которому одобрен Riot Games. Это также делает аналитическую часть воспроизводимой и тестируемой.

## Быстрый старт

Нужен Python 3.11 или новее. Внешних Python-зависимостей нет.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp team.example.json team.json
# Заполните реальные UUID последних трёх актов в team.json.
tracker-report --config team.json --matches data/example_matches.json --output reports
```

Пример конфигурации уже содержит перечисленные Riot IDs. Твинк `sylvain#2567` указан как alias основного аккаунта `AR artzsh#AMBER`: его матчи будут объединены со статистикой основного игрока. Замените значения `replace-with-act-id-*` на UUID нужных трёх актов из вашего разрешённого источника данных.

## Формат входного JSON

Верхний уровень — объект с массивом `matches` или непосредственно массив матчей. При объединении экспортов с нескольких профилей можно оставить дубликаты: записи автоматически дедуплицируются по `match_id`.

```json
{
  "matches": [
    {
      "match_id": "unique-match-id",
      "act_id": "riot-act-uuid",
      "started_at": "2026-05-31T18:30:00Z",
      "map": "Ascent",
      "winning_team": "blue",
      "participants": [
        {
          "riot_id": "AR artzsh#AMBER",
          "team": "blue",
          "agent": "Omen",
          "role": "controller"
        }
      ]
    }
  ]
}
```

Поддерживаемые роли: `controller`, `duelist`, `initiator`, `sentinel`, `unknown`. Любое неизвестное значение нормализуется в `unknown`.

## Выходные файлы

Команда создаёт каталог отчётов со следующими файлами:

| Файл | Назначение |
| --- | --- |
| `summary.md` | Краткий человекочитаемый отчёт. |
| `combinations.csv` | Статистика всех наблюдавшихся подмножеств совместно игравших участников команды. Например, матч втроём учитывается для тройки, входящих в неё пар и отдельных игроков. |
| `player_roles.csv` | Статистика игрока в разрезе ролей. |
| `full_stack_role_matrix.csv` | Одна строка на матч полным стаком; колонки игроков содержат сыгранные роли. |

## Тесты

```bash
python -m unittest discover -s tests -v
```

## Ручной импорт scoreboard HTML

Если разрешённого API пока нет, JSON не нужно заполнять вручную. Откройте матч в браузере, скопируйте HTML двух блоков scoreboard с классом `st-content` в UTF-8 файл, например `html/match-001.html`, и запустите локальный импортёр. Импортёр не обращается к Tracker.gg: он разбирает только сохранённый вами файл.

В scoreboard-фрагменте нет метаданных матча, поэтому их нужно передать аргументами: уникальный ID матча, UUID акта, дату и время, карту и победившую сторону. Первый блок `st-content` считается командой `blue`, второй — `red`. Если вы скопировали только одну сторону, добавьте `--teams blue` или `--teams red`.

### PowerShell

```powershell
New-Item -ItemType Directory -Force html
notepad html\match-001.html
# Вставьте HTML scoreboard, сохраните файл и закройте Блокнот.

tracker-import-html `
  --html html\match-001.html `
  --output data\matches.json `
  --match-id match-001 `
  --act-id replace-with-act-id-1 `
  --started-at 2026-05-31T18:30:00Z `
  --map Ascent `
  --winning-team blue

tracker-report --config team.json --matches data\matches.json --output reports
```

Повторяйте `tracker-import-html` для каждого матча. Файл `data\matches.json` создаётся автоматически; существующие матчи сохраняются, а повторный импорт того же `--match-id` обновляет запись вместо создания дубликата.

### Соответствие агентов и ролей

Роль определяется автоматически по агенту из HTML. Неизвестный будущий агент не ломает импорт: для него сохраняется роль `unknown`, после чего таблицу можно дополнить.

| Role | Agents |
| --- | --- |
| `controller` | Astra, Brimstone, Clove, Harbor, Miks, Omen, Viper |
| `duelist` | Iso, Jett, Neon, Phoenix, Raze, Reyna, Waylay, Yoru |
| `initiator` | Breach, Fade, Gekko, KAY/O, Skye, Sova, Tejo |
| `sentinel` | Chamber, Cypher, Deadlock, Killjoy, Sage, Veto, Vyse |

## Пакетный импорт сохранённых MHTML-страниц в CSV

Для накопления реальных данных удобнее сохранять открытые страницы матчей целиком через браузер: `Ctrl+S` → формат `Веб-страница, один файл (*.mhtml)`. Сложите файлы с разных аккаунтов в одну локальную папку `mhtml`; вложенные папки также обрабатываются. Новый пакетный импортёр извлекает метаданные матча и scoreboard, оставляет только игроков из `team.json` и дописывает строки в `data/team_matches.csv`.

```powershell
New-Item -ItemType Directory -Force mhtml
# Сохраните страницы матчей в папку mhtml, затем выполните:
tracker-import-mhtml-folder --input mhtml --config team.json --output data\team_matches.csv
```

При первом запуске CSV создаётся автоматически. При следующих запусках существующий CSV дополняется. Если один матч сохранён несколько раз — например, со страниц разных участников команды — повторные MHTML пропускаются по `match_id`. Уже присутствующие в CSV матчи также не записываются повторно.

CSV содержит по одной строке на участника вашей команды в каждом матче:

| Группа | Колонки |
| --- | --- |
| Матч | `match_id`, `started_at`, `mode`, `map`, `duration`, `average_rank` |
| Результат | `team`, `team_score`, `opponent_score`, `score`, `result` |
| Игрок | `player`, `riot_id`, `agent`, `role`, `account_level`, `match_rank` |
| Статистика | `trs`, `acs`, `kills`, `deaths`, `assists`, `kd_diff`, `kd`, `damage_delta`, `adr`, `headshot_pct`, `kast_pct`, `first_kills`, `first_deaths`, `multikills` |

`player` — канонический Riot ID из `team.json`. `riot_id` — фактический ID из матча. Поэтому игры на твинке сохраняются под основным игроком, но исходный Riot ID не теряется.
