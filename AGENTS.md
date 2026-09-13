# Live Creator — рабочие правила

## Назначение

Live Creator разрабатывается как самостоятельное экспериментальное приложение в ветке `live-creator`.

Основная ветка UNO Pro Advanced `main` не должна получать промежуточные изменения и сборки Live Creator.

Цель архитектуры — создать универсальное LIVE / SONG окружение, которое позже можно интегрировать обратно в UNO Pro Advanced и адаптировать для других MIDI-устройств.

## Архитектура

Проект разделяется на универсальное ядро и адаптеры.

### `live_creator/core`
Универсальная логика:
- Song arrangement model
- Song Steps
- Preset Blocks
- EMPTY
- ripple editing
- timeline state
- 8x8 logical performance grid
- selection
- playhead
- range selection
- transport state

`core` не должен зависеть от UNO Synth Pro, `.unosyp`, `.unosong` или конкретного MIDI-контроллера.

### `live_creator/ui`
Интерфейс приложения:
- LIVE page
- SONG CREATOR timeline
- 8x8 Performance Grid
- transport
- inspector / selection state

### `live_creator/controllers`
Адаптеры внешних MIDI-контроллеров.

Первый контроллер:
- Novation Launchpad

Launchpad должен управлять теми же функциями, которыми управляет GUI, а не содержать отдельную бизнес-логику.

### `live_creator/devices`
Адаптеры конкретных MIDI-устройств.

Первое устройство:
- UNO Synth Pro

UNO-специфичная логика должна находиться здесь, а не в generic core.

## LIVE

Главная рабочая страница называется `LIVE`.

LIVE содержит:
- SONG CREATOR
- transport
- 8x8 Performance Grid
- состояние текущего Song Step
- текущий preset
- playhead

SONG не является отдельной большой страницей.

`.unosong` является форматом данных UNO-адаптера, а SONG CREATOR является универсальным редактором аранжировки.

## SONG CREATOR

SONG CREATOR — компактная динамическая область timeline.

Не показывать 64 больших слота заранее.

Длина песни определяется фактическим содержимым.

Для UNO-режима максимальная длина — 64 Song Steps.

### Song Step

Song Step — одна дискретная позиция аранжировки.

Абсолютный номер Song Step не является свойством Preset Block.

Номера рассчитываются динамически из:
- порядка элементов
- длины каждого элемента

### Preset Block

Preset Block — визуальное представление одного preset, занимающего один или несколько последовательных Song Steps.

Пример:

`Bass01 x3`

занимает:

`01-03`

Preset Block можно:
- выбирать
- перемещать
- растягивать вправо
- сокращать
- заменять другим preset

### Ripple editing

Сдвиг Preset Block вправо или влево должен сдвигать вместе с ним все последующие элементы.

Изменение длины блока также автоматически сдвигает и перенумеровывает всё последующее содержимое.

Не допускать наложения блоков.

Если операция приводит к длине более 64 Song Steps в UNO-режиме:
- операция запрещается
- ничего не обрезается
- UI показывает `64-step limit reached`

### INSERT / REPLACE

Drop preset между блоками:
- INSERT

Drop preset на существующий блок:
- REPLACE
- длина блока сохраняется

## EMPTY

EMPTY представляет паузу длиной один или несколько Song Steps.

Визуально EMPTY должен выглядеть как узкий пустой промежуток, а не как большой preset block.

EMPTY создаётся главным образом сдвигом блока вправо.

Дополнительно допустимы команды:
- Insert pause before
- Insert pause after

EMPTY можно:
- растягивать
- сокращать
- удалять сдвигом соседних блоков

Количество EMPTY Song Steps должно быть видно через вычисляемый номер или диапазон.

## Нумерация

Над Preset Block и EMPTY показывать вычисляемый диапазон Song Steps.

Примеры:

`01-03`

`04-05`

`06`

При изменении длины или порядка номера должны обновляться автоматически.

## 8x8 Performance Grid

Под SONG CREATOR располагается поле 8x8.

Grid логически представляет максимум 64 Song Steps.

Пример:

pad 01 -> Song Step 01

pad 64 -> Song Step 64

Grid и timeline являются двумя представлениями одной и той же аранжировки.

Выбор элемента в timeline должен отражаться в grid.

Выбор pad в grid должен отражаться в timeline.

Неиспользуемые Song Steps должны отображаться как неактивные.

Во время playback текущий Song Step должен визуально выделяться.

## Launchpad

Novation Launchpad интегрируется как controller adapter поверх 8x8 Performance Grid.

Launchpad не должен напрямую управлять внутренними структурами UNO.

Сначала реализуется virtual 8x8 grid в приложении.

После этого Launchpad подключается к тем же публичным действиям:
- select step
- play from here
- stop
- range selection
- transport
- другие LIVE-команды

## Playback concepts

Предусмотреть архитектурно:
- PLAY
- STOP
- PLAY FROM HERE
- PLAY RANGE
- playhead
- preview preset

Полная реализация playback выполняется после стабилизации модели SONG CREATOR.

## `.unosong`

`.unosong` — внутренний формат UNO Pro Advanced / UNO device adapter.

Это не официальный формат IK Multimedia.

`.unosong` должен быть самодостаточным.

Он не должен зависеть от:
- абсолютных путей
- относительных путей
- текущего состояния внешней preset library
- имён внешних файлов

Внутри `.unosong` хранить:
- manifest
- arrangement
- embedded original raw `.unosyp`

Raw `.unosyp` должны сохраняться без декодирования и повторной сборки.

Не терять:
- неизвестные поля
- переменную длину
- данные после step 16

Используемые preset должны адресоваться через внутренние `preset_id`.

Одинаковые embedded `.unosyp` допускается дедуплицировать по содержимому, например SHA-256.

Library используется только как источник при добавлении или замене preset.

Сохранённый `.unosong` должен работать даже если исходный `.unosyp`:
- перемещён
- переименован
- удалён

## UNO Synth Pro

UNO Synth Pro является первым device adapter, но не частью универсального core.

Использовать существующую проверенную логику загрузки preset из UNO Pro Advanced там, где это возможно.

Не создавать параллельную несовместимую реализацию preset loader без необходимости.

## Безопасность MIDI

Не придумывать неподтверждённые MIDI/SysEx-команды.

STORE и команда `0x28` остаются заблокированными.

SEQ ON/OFF не изменять без подтверждённого аппаратного мэппинга.

Диагностические тесты не должны отправлять разрушительные команды.

`IMPLEMENTED` не означает `HARDWARE PASS`.

## COPY / PASTE

COPY / PASTE в GUI SONG / LIVE не нужны.

Если соответствующие кнопки присутствуют в перенесённом UNO UI, их не реализовывать — удалить.

## Сборки

Live Creator имеет собственную версионную линию.

Пример:

- `v0.1-alpha`
- `v0.2-alpha`
- `v0.3-alpha`

Не увеличивать версию основного UNO Pro Advanced из-за промежуточных Live Creator сборок.

Новые сборки создавать только по явной команде пользователя.

## Интеграция обратно в UNO Pro Advanced

Live Creator должен проектироваться так, чтобы generic core можно было интегрировать обратно в основной проект без полного переписывания.

Желаемая зависимость:

UNO Pro Advanced
-> Live Creator core
-> UNO device adapter

а не копирование двух независимых реализаций SONG.
