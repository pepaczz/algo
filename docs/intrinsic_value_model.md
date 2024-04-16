
# Intrinsic value model

The intrinsic value model is based on the discounted cash flow (DCF) model. 

### WACC calculation

1. Cost of Debt:

$$\text{Cost of Debt} = \frac{\text{Interest Expense}}{\text{Total Long-Term Debt}}$$



2. Effective Tax Rate:

$$\text{Effective Tax Rate} = \frac{\text{Income Tax Expense}}{\text{Pretax Income}}$$


3. Cost of Debt after Tax:

$$\text{Cost of Debt after Tax} = \text{Cost of Debt} \times (1 - \text{Effective Tax Rate})$$


4. Cost of Equity:

$$\text{Cost of Equity} = \text{Risk-Free Rate} + \beta \times \text{Equity Risk Premium}$$


5. Market Capitalization:

$$\text{Market Cap} = \text{Share Price} \times \text{Shares Outstanding}$$


6. Weight of Debt:

$$\text{Weight of Debt} = \frac{\text{Total Long-Term Debt}}{\text{Total Debt} + \text{Market Cap}}$$


7. Weight of Equity:

$$\text{Weight of Equity} = \frac{\text{Market Cap}}{\text{Total Debt} + \text{Market Cap}}$$


8. Weighted Average Cost of Capital (WACC):

$$\text{WACC} = (\text{Weight of Debt} \times \text{Cost of Debt after Tax}) + (\text{Weight of Equity} \times \text{Cost of Equity})$$

### Free cash flow to firm

1. After-Tax Operating Income:

$$\text{After-Tax Operating Income} = \text{Operating Income} \times (1 - \text{Effective Tax Rate})$$


2. Reinvestment:

$$\text{Reinvestment} = \text{Capex} + (\text{Net Cash from Operating Activities} - \text{Net Income} - \text{Share-Based Compensation})$$


3. Free Cash Flow to Firm (FCFF):

$$\text{FCFF} = \text{After-Tax Operating Income} + \text{Reinvestment}$$

### Intrinsic value


1. FCFF Projection:

$$\text{FCFF}_{\text{Projection}} = [\text{FCFF} \times (1 + \text{Growth Rate})^i] \text{ for } i \text{ in range}(1, 6)$$


2. Terminal Value:

$$\text{Terminal Value} = \text{FCFF Projection}_{\text{Last}} \times \left( \frac{1 + \text{Perpetual Growth Rate}}{\text{WACC} - \text{Perpetual Growth Rate}} \right)$$


3. Enterprise Value:

$$\text{Enterprise Value} = \text{NPV}(\text{WACC}, [0] + \text{FCFF Projection})$$


4. Equity Value:

$$\text{Equity Value} = \text{Enterprise Value} + \left( \text{Cash and Cash Equivalents} - (\text{Current Debt} + \text{Total Long-Term Debt}) \right)$$


5. Intrinsic Value per Share:

$$\text{Intrinsic Value per Share} = \frac{\text{Equity Value}}{\text{Shares Outstanding}}$$
