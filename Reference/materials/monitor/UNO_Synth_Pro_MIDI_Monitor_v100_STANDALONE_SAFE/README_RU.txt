UNO Synth Pro MIDI Monitor v1.0 — ОТДЕЛЬНОЕ ПРИЛОЖЕНИЕ
=======================================================

Это самостоятельный MIDI/SysEx Monitor/Proxy.
Он больше НЕ является частью сборок UNO Synth Pro Editor.

Запуск:
  run_monitor.bat

Маршрутизация:
  Official IK Editor MIDI OUTPUT -> UNO_TAP
  Official IK Editor MIDI INPUT  <- UNO_RETURN

  Monitor Physical UNO INPUT      = UNO Synth Pro
  Monitor Physical UNO OUTPUT     = UNO Synth Pro
  Monitor EDITOR OUT / TAP INPUT  = UNO_TAP
  Monitor EDITOR IN / RETURN OUT  = UNO_RETURN

ВАЖНО:
- UNO_TAP и UNO_RETURN должны быть двумя разными loopMIDI-портами.
- F8 MIDI Clock СКРЫТ из capture/log по умолчанию.
- FE Active Sense СКРЫТ из capture/log по умолчанию.
- Скрытые F8/FE всё равно ПРОХОДЯТ через Proxy без изменения.
- Захват Clock/Active Sense можно включить чекбоксами.

STOP MIDI:
- кнопка STOP MIDI
- Ctrl+Shift+Esc — основная комбинация
- Ctrl+Shift+F12 — резервная комбинация, потому что Windows может перехватывать Ctrl+Shift+Esc для Task Manager.

STOP MIDI:
1) немедленно запрещает новые MIDI forwarding операции;
2) останавливает MIDI IN;
3) сбрасывает MIDI OUT;
4) очищает очередь ожидающих forwarding-сообщений;
5) закрывает WinMM-порты в фоне, не заставляя GUI ждать драйвер;
6) НЕ запускает Proxy снова автоматически.

Архитектурные изменения против v0.7:
- WinMM callback больше не вызывает Tkinter;
- WinMM callback не отправляет SysEx напрямую;
- forwarding выполняется отдельным worker-потоком;
- GUI получает capture пакетами через thread-safe queue;
- один F8 больше не создаёт отдельный Tk callback;
- в таблице максимум 5000 строк, но полный отфильтрованный capture хранится до Clear/закрытия и сохраняется в TXT;
- дополнительные проверки против перепутанных UNO_TAP / UNO_RETURN.

Если Windows снова теряет ввод мыши/клавиатуры:
1) не продолжать тест;
2) попробовать Ctrl+Shift+F12 или STOP MIDI;
3) закрыть официальный Editor и Monitor;
4) сообщить, в какой момент это произошло и какие порты были выбраны.
