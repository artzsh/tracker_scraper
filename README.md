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
