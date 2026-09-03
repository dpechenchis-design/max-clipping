# Доказова база — розбір 9 готових кліпів Max

Правила у `SKILL.md` виведені звідси, а не вигадані. Кліпи розібрані машинно:
`analyze_examples.py` дав тривалість, точки внутрішніх різів (scdet по смузі
самого відео) і пословний транскрипт; шапки зчитані з кадру.

Прислано 10 файлів, `example 1` і `example 5` — байт-в-байт однакові (md5
`251dcac0…`), тож унікальних дев'ять.

## Зведення

| кліп | с | фрагм | тип | хук |
|---|---|---|---|---|
| ex8 | 23 | 2 | qa | *How'd you feel taking pictures before versus now?* |
| ex7 | 23 | 4 | qa | *You used to kind of feel like the fat friend, and now you don't?* |
| ex1 | 27 | 1 | framework | *I've always found the belief three days, three weeks, three months…* |
| ex10 | 27 | 2 | qa | *What would their day-to-day life be like right now?* |
| ex6 | 49 | 1 | framework | *The biggest struggle I faced while losing weight was definitely…* |
| ex9 | 59 | 6 | qa | *What would you say to someone that says they don't have time…* |
| ex2 | 79 | 3 | story | *Oh yeah, I'm not living past 40.* |
| ex4 | 88 | 4 | story | *I'm [ім'я]. I'm a [професія] over at [компанія].* |
| ex3 | 102 | 10 | story | *There wasn't necessarily a good balance in my life…* |

Тривалість 23-102 с, медіана 49 с. Щільність мови 2.5-3.4 слова/с у всіх дев'яти —
рівна, тобто ріжуть по думці, а не під хронометраж.

## Гості та шапки

П'ять гостей, у кожного свій колір хайлайту і постійний заголовок.
Імена прибрані — це приватні особи, а правила відбору від імен не залежать.

| гість | заголовок | колір | кліпи |
|---|---|---|---|
| гість A | `-75LBS IN 11 MONTHS` | зелений | ex1, ex4 |
| гість B | `-80LBS IN 11 MONTHS` | жовтий | ex2, ex9, ex10 |
| гість C | `-62LBS IN 13 MONTHS` | помаранчевий | ex3 |
| гість D | `-50LBS IN 20 MONTHS` | блакитний | ex6 |
| гість E | `-161LBS IN 17 MONTHS` | червоний | ex7, ex8 |

Підзаголовки, всі дев'ять. **Ми їх не пишемо** — це робота монтажера, скіл
віддає тільки сирі кліпи. Наведені як доказ того, що в кожному кліпі є одна
самодостатня фраза; саме це і є фільтр відбору.

| кліп | підзаголовок | спосіб |
|---|---|---|
| ex1 | 3 days to start, 3 weeks for consistency, 3 months to lock it in | перефраз |
| ex2 | my doctor said my body was working way harder than it should at 25 | перефраз поворотної точки |
| ex3 | from 205 to a weight he's never seen in his adult life | перефраз, цифри з кліпа |
| ex4 | no longer feeling like the "biggest dude in the room" | перефраз навколо цитати |
| ex6 | the 3 things that kept me stuck for years | перефраз, називає структуру |
| ex7 | "I was the fat friend… but not anymore" | дослівна цитата |
| ex8 | "they're not wrapping their hands around another half of a person…" | дослівна цитата |
| ex9 | how I built a routine that was actually sustainable | перефраз |
| ex10 | "I don't wanna think about what it'd be like if I hadn't taken this leap" | дослівна цитата |

Шість перефразів, три дослівні цитати. Обидва способи беруть матеріал **з тіла
кліпа** — нічого не додається ззовні.

## Де стоять різи

**Q&A — різ на межі питання й відповіді.** ex8 різ на 2.77 с одразу після
*«How'd you feel taking pictures before versus now?»*. ex10 — 2.1 с. ex7 — 3.23 с.
ex9 — 4.5 с. Тобто питання лишається цілим, а пауза перед відповіддю вирізається.

**Framework — різів нема взагалі.** ex1 і ex6 суцільні. Гість сказав набіло,
його не чіпали. Це діагностична ознака: якщо в транскрипті думка викладена з
плутаниною — це не framework.

**Story — франкенштейн.** ex3 має 9 внутрішніх різів (1.1, 11.1, 14.87, 31.17,
75.13, 84.87, 88.97, 99.17, 102.03) — п'ять тематичних блоків з різних місць
інтерв'ю:

```
0–11    проблема: нема балансу, сидячий спосіб життя
11–31   провалені спроби рахувати калорії, «fell out of it in like a week»
31–75   цілі й цифри: 205 → 175 → 150, May 2025 → February 2026
75–84   чого бракувало: accountability
84–102  що спрацювало: people pleaser + support system
```

ex9 має 5 різів, але вони збиті в купу на початку (4.5, 7.03, 8.6, 8.7, 9.93) —
це не збірка, а вичищання заминок навколо початку відповіді.

## Кінцівки — усі дев'ять

Жодна не обірвана на півдумці.

| кліп | остання фраза | тип кінцівки |
|---|---|---|
| ex1 | *It's just momentum at that point, inertia.* | закриття фреймворку |
| ex2 | *…accept the help from you and the program and just give you those tools.* | плаг програми |
| ex3 | *…having someone that's like, do the thing, or else I'm gonna be sad.* | панчлайн |
| ex4 | *…allows you to be more free, open and honest with people.* | емоційний пейофф |
| ex6 | *…the love that they have for you is always going to come in the form of take a break from a diet.* | панчлайн-інсайт |
| ex7 | *…average good-looking guy that can still progress to better and good opportunities.* | пейофф ідентичності |
| ex8 | *Feels pretty good.* | короткий пейофф |
| ex9 | *Just commit to doing it and he's gonna work with you… So it's, yeah, just do it.* | CTA |
| ex10 | *I could not be more grateful. So thank you, Max, honest to God, thank you.* | подяка коучу |

## Тематичні кошики

| кошик | де видно |
|---|---|
| заперечення | ex9 — «нема часу» |
| зсув ідентичності | ex7 fat friend, ex8 фото до/після, ex4 biggest dude in the room |
| метод | ex1 звички, ex6 три перепони, ex4 трекінг даних |
| цифри і пруф | ex3 205→150, ex4 320→244.2 |
| ставки і страх | ex2 подагра в 25, «not living past 40» |
| контрфактичне і вдячність | ex10 |

## Технічне

Усі дев'ять: 720×1280, h264, 30 fps, aac. Відео 16:9 всередині чорних полів,
шапка зверху, караоке-субтитри по одному слову знизу. Це робить монтажер —
скіл віддає чисті шматки.
