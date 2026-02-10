# Data Tree Structure

```
system/
├── A-Level/
│   ├── Accounting/
│   │   ├── AQA Accounting (7127)/
│   │   ├── Cie Accounting (9706)/
│   │   └── Edexcel Accounting (9AC0)/
│   ├── Biology/
│   │   ├── AQA Biology (7402)/
│   │   ├── Cie Biology (9700)/
│   │   └── Edexcel Biology (9BI0)/
│   ├── Business/
│   │   ├── AQA Business (7132)/
│   │   ├── Cie Business (9609)/
│   │   └── Edexcel Business (9BS0)/
│   ├── Chemistry/
│   │   ├── AQA Chemistry (7405)/
│   │   ├── Cie Chemistry (9701)/
│   │   └── Edexcel Chemistry (9CH0)/
│   ├── Computer Science/
│   │   ├── AQA Computer Science (7517)/
│   │   └── Cie Computer Science (9618)/
│   ├── Design Technology/
│   │   ├── AQA Design Technology (7552)/
│   │   └── Edexcel Design Technology Product Design (9DT0)/
│   ├── Economics/
│   │   ├── AQA Economics (7136)/
│   │   ├── Cie Economics (9708)/
│   │   └── Edexcel Economics (9EC0)/
│   ├── Engineering/
│   │   └── AQA Engineering (8852)/
│   ├── English Language/
│   │   ├── AQA English Language (7702)/
│   │   ├── Cie English Language (9093)/
│   │   └── Edexcel English Language (9EN0)/
│   ├── English Literature/
│   │   ├── AQA English Literature (7712)/
│   │   ├── Cie Literature English (9695)/
│   │   └── Edexcel English Literature (9ET0)/
│   ├── Food Science Nutrition/
│   │   └── AQA Food Science Nutrition (7272)/
│   ├── French/
│   │   └── AQA French (7652)/
│   ├── Further Mathematics/
│   │   ├── AQA Further Mathematics (7367)/
│   │   ├── Cie Further Mathematics (9231)/
│   │   └── Edexcel Further Mathematics (9FM0)/
│   ├── Geography/
│   │   ├── AQA Geography (7037)/
│   │   ├── Cie Geography (9696)/
│   │   └── Edexcel Geography (9GE0)/
│   ├── Global perspectives/
│   │   └── Cie Global Perspectives Research (9239)/
│   ├── History/
│   │   ├── AQA History (7041)/
│   │   ├── AQA History (7042)/
│   │   ├── Cie History (9389)/
│   │   ├── Cie History (9489)/
│   │   └── Edexcel History (9HI0)/
│   ├── Information Technology/
│   │   └── Edexcel Information Technology (9IT0)/
│   ├── Mathematics/
│   │   ├── AQA Mathematics (7357)/
│   │   ├── Cie Mathematics (9709)/
│   │   └── Edexcel Mathematics (9MA0)/
│   ├── Physical Education/
│   │   ├── AQA Physical Education (7357)/
│   │   ├── AQA Physical Education (7582)/
│   │   └── Edexcel Physical Education (9PE0)/
│   ├── Physics/
│   │   ├── AQA Physics (7408)/
│   │   ├── Cie Physics (9702)/
│   │   └── Edexcel Physics (9PH0)/
│   ├── Psychology/
│   │   ├── AQA Psychology (7182)/
│   │   ├── Cie Psychology (9990)/
│   │   └── Edexcel Psychology (9PS0)/
│   └── Sociology/
│       ├── AQA Sociology (7192)/
│       ├── Cie Sociology (9699)/
│       └── Edexcel Sociology (9SC0)/
├── HKDSE/
│   ├── Biology/
│   ├── Business, Accounting and Financial Studies/
│   ├── Chemistry/
│   ├── Chinese History/
│   ├── Chinese Language/
│   ├── Chinese Literature/
│   ├── Citizenship and Social Development/
│   ├── Design and Applied Technology/
│   ├── Economics/
│   ├── English Language/
│   ├── Ethics and Religious Studies/
│   ├── Geography/
│   ├── Health Management and Social Care/
│   ├── History/
│   ├── Information and Communication Technology/
│   ├── Literature in English/
│   ├── Mathematics/
│   ├── Music/
│   ├── Physical Education/
│   ├── Physics/
│   ├── Technology and Living/
│   ├── Tourism and Hospitality Studies/
│   └── Visual Arts/
├── IB/
│   ├── Biology/
│   ├── Business Management/
│   ├── Chemistry/
│   ├── Computer Science/
│   ├── Design Technology/
│   ├── Economics/
│   ├── English A Language Literature/
│   ├── Environmental Systems Societies/
│   ├── Film/
│   ├── Geography/
│   ├── Global Politics/
│   ├── History/
│   ├── Mathematics AA/
│   ├── Music/
│   ├── Physics/
│   ├── Psychology/
│   ├── Spanish B/
│   ├── Theory of Knowledge/
│   └── Visual Arts/
├── IGCSE/
│   ├── Accounting/
│   │   ├── Cie Accounting (0452)/
│   │   ├── Edexcel Accounting/
│   │   └── Edexcel Accounting (4AC1)/
│   ├── Additional Mathematics/
│   │   ├── Cie Additional Mathematics (0606)/
│   │   ├── Edexcel Further Mathematics/
│   │   └── Edexcel Mathematics (4MA0)/
│   ├── Biology/
│   │   ├── Cie Biology (0610)/
│   │   └── Edexcel Biology (4BI1)/
│   ├── Business/
│   │   ├── Cie Business (0450)/
│   │   └── Edexcel Business (4BS1)/
│   ├── Business Studies/
│   │   ├── Cie Business (0450)/
│   │   └── Edexcel Business (4BS1)/
│   ├── Chemistry/
│   │   ├── Cie Chemistry (0620)/
│   │   └── Edexcel Chemistry (4CH1)/
│   ├── Chinese First Language/
│   │   ├── Cie Chinese First Language (0509)/
│   │   └── Edexcel Chinese (4CN0)/
│   ├── Chinese Mandarin Foreign Language/
│   │   ├── Cie Chinese Mandarin Foreign Language (0547)/
│   │   └── Edexcel Chinese (4CN0)/
│   ├── Chinese Second Language/
│   │   ├── Cie Chinese Second Language (0523)/
│   │   └── Edexcel Chinese (4CN0)/
│   ├── Combined Science/
│   │   ├── Cie Combined Science (0653)/
│   │   └── Edexcel Science (Double Award) (4SC0)/
│   ├── Computer Science/
│   │   ├── Cie Computer Science (0478)/
│   │   └── Edexcel Computer Science (4CP0)/
│   ├── Design Technology/
│   │   └── Cie Design Technology (0445)/
│   ├── Economics/
│   │   ├── Cie Economics (0455)/
│   │   ├── Edexcel Economic/
│   │   └── Edexcel Economics/
│   ├── English Literature/
│   │   ├── Cie Literature English (0475)/
│   │   └── Edexcel English literature (4ET1)/
│   ├── English Second Language/
│   │   ├── Cie English Second Language (0510)/
│   │   └── Edexcel English as a Second Language (4ES0)/
│   ├── Enterprise/
│   │   └── Cie Enterprise (0454)/
│   ├── Environmental Management/
│   │   └── Cie Environmental Management (0680)/
│   ├── First Language English/
│   │   ├── Cie First Language English (0500)/
│   │   └── Edexcel English Language (4EA0)/
│   ├── Food and Nutrition/
│   │   └── Cie Food and Nutrition (0648)/
│   ├── Geography/
│   │   ├── Cie Geography (0460)/
│   │   └── Edexcel Geography (4GE1)/
│   ├── Global Perspectives/
│   │   └── Cie Global Perspectives (0457)/
│   ├── History/
│   │   ├── Cie History (0470)/
│   │   └── Edexcel History (4HI1)/
│   ├── Human Biology/
│   │   └── Edexcel Human Biology/
│   ├── ICT/
│   │   ├── Cie ICT (0417)/
│   │   └── Edexcel ICT (4IT1)/
│   ├── International Mathematics/
│   │   ├── Cie Mathematics - International (0607)/
│   │   └── Edexcel Mathematics (4MA0)/
│   ├── Mathematics/
│   │   ├── Cie Mathematics (0580)/
│   │   └── Edexcel Mathematics (4MA1)/
│   ├── Physical Education/
│   │   └── Cie Physical Education (0413)/
│   ├── Physical Science/
│   │   └── Cie Physical Science (0652)/
│   ├── Physics/
│   │   ├── Cie Physics (0625)/
│   │   └── Edexcel Physics (4PH1)/
│   ├── Psychology/
│   │   └── Cie Psychology (0990)/
│   └── Sociology/
│       └── Cie Sociology (0495)/
├── primary/
└── secondary/