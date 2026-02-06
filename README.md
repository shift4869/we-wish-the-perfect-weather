# we-wish-the-perfect-weather

## "完璧な気候" かどうかを判定してDBに記録していく気象記録システム
- "完璧な気候" の定義
  - 気温18度以上28度以下、かつ湿度40%以上70%以下
    - 事務所衛生基準規則第5条より
    - https://jsite.mhlw.go.jp/yamanashi-roudoukyoku/hourei_seido_tetsuzuki/anzen_eisei/hourei_seido/jimushosoku_kaisei_00001.html
    - https://laws.e-gov.go.jp/law/347M50002000043/#Mp-Ch_5
  - 降水量が0または降水確率が10%以下=天気が雨または雪でない
    - 晴れか曇りかは問わない
  - 風速3m/s以下（木の葉や細かい小枝が揺れる程度で、日常生活にはほとんど影響がない程度）
  - 花粉飛散数が10個/cm^2未満（花粉数「少ない」の基準）
    - 元データとしてはウェザーニュースの「ポールンロボ」で観測されたデータを使用（元データの項目を参照）
    - 花粉情報等標準化委員会が制定した基準より
    - https://square.umin.ac.jp/psj3/jp/PSJ_polleninfo_standardization.pdf

## 元データ
- [Open-Meteo](https://open-meteo.com/)
- [花粉飛散数API](https://wxtech.weathernews.com/products/data/api/operations/opendata/getPollenCounts/)

## License/Author
[MIT License](https://github.com/shift4869/we-wish-the-perfect-weather/blob/master/LICENSE)  
Copyright (c) 2025 ~  [shift](https://x.com/_shift4869)
