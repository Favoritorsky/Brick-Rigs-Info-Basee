# Электроника и логика

## Скорость логики (проверено тестом в игре)
- Логика обновляется **каждый кадр** (у автора ~120–150 FPS).
- Цепочка блоков считается **мгновенно**, за один кадр (задержка на блок = 0).
- Следствия: длинные цепочки не тормозят; но цепочки регистров «сосед берёт у соседа» пролетают насквозь за кадр — нужен двухфазный сдвиг (см. ниже).
- Скорость, привязанная к кадрам, меняется вместе с FPS. Для стабильной скорости тактировать по сенсору `Time`.

## Входы блоков
- У мат-блока входы A, B (и C для `Clamp`/`Lerp`). Вход = **сумма** всех подключённых блоков (`SourceBricks`) или константа.
- `InputAxis`: `Custom` — провода; `AlwaysOn` + `Value` — **константа**; `None`; оси кресла (`Steering`, `Throttle`, `Action1`, `HandBrake`, `ViewPitch`…).
- По умолчанию у мат-блока A = провода, B = константа 1.0; у лампы вход = `Headlight` (поменять на `Custom`!); у сенсора выход ограничен −1..1 — для больших чисел расширять `OutputChannel` (MinIn/MaxIn/MinOut/MaxOut).

## Операции мат-блока
Add, Subtract, Multiply, Divide, Fmod, Min, Max, Abs, Sign, Negate, Reciprocal, Square, Sqrt, Power, Exp, Ln, Log10, Round, Ceil, Floor, Fraction, Truncate, Sin/Cos/Tan (+Deg-версии, Asin…, Atan2), Greater, GreaterEqual, Less, LessEqual, Equal, NotEqual, ApproximatelyEqual, **And, Or, Xor, Not**, Saturate, Clamp, ClampSymmetric, Lerp, Remap, **Derivative, Integral, LowPass, RateLimit, Pulse**.

## Сенсоры (`SensorType`)
Speed, NormalSpeed, Acceleration, NormalAcceleration, AngularSpeed, NormalAngularSpeed, Distance, **Time**, DeltaTime, Framerate, **TimeOfDay**, **Proximity**, DistanceToGround, Altitude, AbsAltitude, Pitch, Yaw, Roll, PosX, PosY, NumSeekingProjectiles…
- Сенсор имеет вход включения (`EnabledInputChannel`), `bReturnToZero` — сброс при выключении.
- `Proximity` у игроков — для автоматики: подошёл/подъехал → включились свет, дверь, турель.

## Переключатель (`SwitchBrick`)
- Выход 0/1 (через `OutputChannel` можно сделать 0..N). `bReturnToZero=1` — кнопка (держишь — 1), `0` — тумблер.
- `SwitchName` — подпись при наведении. Переключатель с входом `Custom` работает как преобразователь диапазона.

## Проверенные приёмы
| Приём | Как |
|---|---|
| Регистр (память) | мат-блок Add с входом A = [сам себя, приращение]. Приращение = (новое − текущее) × импульс |
| Импульс 1 кадр | сенсор Time, включение = сигнал, `MinIn=MaxIn=0.001`, `MinOut=1`, `MaxOut=0`, `bReturnToZero` (или операция `Pulse`) |
| И / ИЛИ / НЕ | `And/Or/Not` или: И = GreaterEqual(сумма, n−0.5), ИЛИ = GreaterEqual(сумма, 0.5) |
| Дешифратор «X == k» | Equal(X, k) |
| Сдвиговый регистр | **двухфазный**: фаза A — каждый копирует себя в буфер, фаза B (другой кадр) — берёт буфер соседа. Иначе при мгновенном расчёте всё пролетает за кадр |
| Такт | счётчик кадров (Add сам себя +1) + Equal(Fmod(счётчик, K), фаза) — или по времени: Fmod(Time×скорость, 1) и окна |
| Выбор строки ПЗУ | Σ Equal(PC, r) × код_r; код строки = команда×1000 + число |
| Сброс | у каждого регистра доп. вход: регистр × (−импульс_сброса) |
| Псевдослучайность | Floor(Abs(Sin(Time×12.9898))×43758.5453), затем Fmod |
| Плавность | LowPass / RateLimit |

## Экраны из ламп
- Пиксель = лампа (или 3 RGB-слоя). Для объекта: Equal(X,c)×Equal(Y,r) на пиксель.
- Скроллинг: сдвиговый регистр столбцов + ПЗУ одного входящего столбца (не пересчитывать весь экран).
- Цвет кодом: R + 4G + 16B (по 0..3), декодер Fmod/Subtract на пиксель.
