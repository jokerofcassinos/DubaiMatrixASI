<chart>
id=0
symbol=
period_type=0
period_size=5
digits=5
tick_size=0.000000
position_time=0
scale_fix=0
scale_fixed_min=0.000000
scale_fixed_max=0.000000
scale_fix11=0
scale_bar=0
scale_bar_val=0.000000
scale=4
mode=1
fore=0
grid=1
volume=0
scroll=1
shift=1
shift_size=20
fixed_pos=0.000000
ohlc=1
one_click=0
one_click_btn=0
bidline=1
askline=0
lastline=1
days=0
descriptions=0
tradelines=1
tradehistory=0
window_left=0
window_top=0
window_right=0
window_bottom=0
window_type=0
background_color=2234131
foreground_color=12498354
barup_color=10135078
bardown_color=5264367
bullcandle_color=10135078
bearcandle_color=5264367
chartline_color=12498354
volumes_color=10135078
grid_color=2957854
bidline_color=16736809
askline_color=3556340
lastline_color=8813432
stops_color=39167
windows_total=7

<window>
height=42.000000
objects=0

<indicator>
name=Main
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1
</indicator>

<indicator>
name=Moving Average
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=EMA 9
draw=129
style=0
width=2
arrow=251
color=15963681
</graph>
period=9
shift=0
method=1
</indicator>

<indicator>
name=Moving Average
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=EMA 21
draw=129
style=0
width=2
arrow=251
color=28159
</graph>
period=21
shift=0
method=1
</indicator>

<indicator>
name=Moving Average
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=EMA 50
draw=129
style=0
width=1
arrow=251
color=13941760
</graph>
period=50
shift=0
method=1
</indicator>

<indicator>
name=Moving Average
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=EMA 200
draw=129
style=2
width=1
arrow=251
color=12339115
</graph>
period=200
shift=0
method=1
</indicator>

<indicator>
name=Bollinger Bands
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=Bands(20) Middle
draw=129
style=2
width=1
arrow=251
color=16098626
</graph>

<graph>
name=Bands(20) Upper
draw=129
style=1
width=1
arrow=251
color=16098626
</graph>

<graph>
name=Bands(20) Lower
draw=129
style=1
width=1
arrow=251
color=16098626
</graph>

period=20
shift=0
deviations=2.000000
</indicator>

<indicator>
name=Parabolic SAR
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=SAR(0.02, 0.2)
draw=3
style=0
width=1
arrow=159
color=3927039
</graph>
step=0.020000
maximum=0.200000
</indicator>

<indicator>
name=Ichimoku Kinko Hyo
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=Tenkan-sen(9)
draw=1
style=0
width=1
arrow=251
color=10132207
</graph>

<graph>
name=Kijun-sen(26)
draw=1
style=0
width=1
arrow=251
color=16370320
</graph>

<graph>
name=Senkou Span A;Senkou Span B
draw=7
style=0
width=1
arrow=251
color=3308846,2631878
</graph>

<graph>
name=Chikou Span
draw=1
style=2
width=1
arrow=251
color=14193614
</graph>

tenkan=9
kijun=26
senkou=52
</indicator>

</window>

<window>
height=10.000000
objects=0

<indicator>
name=Relative Strength Index
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=1
scale_fix_min_val=0.000000
scale_fix_max=1
scale_fix_max_val=100.000000
expertmode=0
fixed_height=-1

<graph>
name=RSI(14)
draw=1
style=0
width=2
arrow=251
color=16549563
</graph>

<level>
level=85.000000
style=2
color=5264367
width=1
descr=Superaquecimento
</level>

<level>
level=70.000000
style=2
color=4536886
width=1
descr=Sobrecompra
</level>

<level>
level=50.000000
style=3
color=3289650
width=1
descr=Neutro
</level>

<level>
level=30.000000
style=2
color=4536886
width=1
descr=Sobrevenda
</level>

<level>
level=15.000000
style=2
color=5264367
width=1
descr=Congelamento
</level>

period=14
</indicator>

</window>

<window>
height=10.000000
objects=0

<indicator>
name=MACD
path=
apply=1
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=MACD(12,26,9)
draw=2
style=0
width=3
arrow=251
color=13941760
</graph>

<graph>
name=Signal(12,26,9)
draw=1
style=2
width=2
arrow=251
color=28159
</graph>

<level>
level=0.000000
style=2
color=4536886
width=1
descr=Zero
</level>

fast_ema=12
slow_ema=26
signal_sma=9
</indicator>

</window>

<window>
height=10.000000
objects=0

<indicator>
name=Stochastic Oscillator
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=1
scale_fix_min_val=0.000000
scale_fix_max=1
scale_fix_max_val=100.000000
expertmode=0
fixed_height=-1

<graph>
name=%K(14)
draw=1
style=0
width=2
arrow=251
color=15963681
</graph>

<graph>
name=%D(14)
draw=1
style=2
width=1
arrow=251
color=28159
</graph>

<level>
level=80.000000
style=2
color=4536886
width=1
descr=Sobrecompra
</level>

<level>
level=20.000000
style=2
color=4536886
width=1
descr=Sobrevenda
</level>

Kperiod=14
Dperiod=3
slowing=3
method=0
price_apply=0
</indicator>

</window>

<window>
height=10.000000
objects=0

<indicator>
name=Average Directional Movement Index
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=ADX(14)
draw=1
style=0
width=2
arrow=251
color=16549563
</graph>

<graph>
name=+DI(14)
draw=1
style=0
width=1
arrow=251
color=10135078
</graph>

<graph>
name=-DI(14)
draw=1
style=0
width=1
arrow=251
color=5264367
</graph>

<level>
level=25.000000
style=2
color=4536886
width=1
descr=Tendencia Forte
</level>

period=14
</indicator>

</window>

<window>
height=9.000000
objects=0

<indicator>
name=Average True Range
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=ATR(14)
draw=1
style=0
width=2
arrow=251
color=10135078
</graph>

period=14
</indicator>

</window>

<window>
height=9.000000
objects=0

<indicator>
name=Volumes
path=
apply=0
show_data=1
scale_inherit=0
scale_line=0
scale_line_percent=50
scale_line_value=0.000000
scale_fix_min=0
scale_fix_min_val=0.000000
scale_fix_max=0
scale_fix_max_val=0.000000
expertmode=0
fixed_height=-1

<graph>
name=Volumes
draw=11
style=0
width=2
arrow=251
color=10135078,5264367
</graph>
real_volumes=0
</indicator>

</window>
</chart>
