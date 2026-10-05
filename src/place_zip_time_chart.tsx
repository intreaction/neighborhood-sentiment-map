import * as React from 'react';
import {Bar,BarChart,CartesianGrid,Line,LineChart,ReferenceArea,ReferenceLine,XAxis,YAxis} from 'recharts';
import {ChartContainer,ChartLegend,ChartLegendContent,ChartTooltip,ChartTooltipContent} from './components/ui/chart';

const fmt=(v:number,d=0)=>Number.isFinite(v)?v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';

// The selected ZIP across every period in the data, with the periods the map is using shaded.
// Two charts share one time axis instead of one chart with two y-scales.
export function ZipTimeChart({time,zip,cityLabel}:{time:any,zip:string,cityLabel:string}) {
  if(!time?.series?.length)return null;
  const {series,shade,markers,covidIndex,grain,smooth}=time;
  const tick=(i:number)=>series[i]?.label.slice(-4)??'';
  const ticks=series.filter((_:any,i:number)=>i%(grain==='quarter'?4:12)===0).map((p:any)=>p.index);
  const marks=<>
    <ReferenceArea x1={covidIndex} x2={series.length-1} fill="#9ea8a8" fillOpacity={.12} ifOverflow="hidden"/>
    {shade.map(([a,b,kind]:[number,number,string],i:number)=><ReferenceArea key={i} x1={a} x2={b} fill={kind==='level'?'#245c49':'#889686'} fillOpacity={kind==='level'?.16:.18}/>)}
    {markers.map((m:any)=><ReferenceLine key={m.id} x={m.index} stroke="#b56b32" strokeDasharray="3 3"/>)}
  </>;
  const x=<XAxis dataKey="index" type="number" domain={[0,series.length-1]} ticks={ticks} tickFormatter={tick} tickLine={false} axisLine={false} fontSize={10}/>;
  const per=grain==='quarter'?'quarter':smooth>1?`month, ${smooth}-month average`:'month';
  return <div className="mt-6 grid gap-4 rounded-lg border bg-card p-4 md:grid-cols-2">
    <div className="md:col-span-2 flex flex-wrap items-baseline justify-between gap-2">
      <p className="m-0 font-serif text-lg">ZIP {zip} over time</p>
      <p className="m-0 text-[11px] text-muted-foreground">Shaded green: the period the map shows · grey: the period it is compared with · dashed: past-project openings in {cityLabel} · light band: COVID-19 from March 2020</p>
    </div>
    <div><p className="chart-axis-label">Reviews per {grain==='quarter'?'quarter':'month'}</p>
      <ChartContainer config={{reviews:{label:'Reviews',color:'#245c49'}}} className="decision-chart" style={{height:170}} aria-label={`ZIP ${zip}: reviews per period`}>
        <BarChart data={series} margin={{top:5,right:8,left:0,bottom:0}} barCategoryGap={1}>
          <CartesianGrid vertical={false}/>{x}<YAxis width={44} tickLine={false} axisLine={false} fontSize={10} tickFormatter={(v:number)=>fmt(v)}/>
          {marks}
          <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(v:any,_n:any,item:any)=><div><strong>{item.payload.label}</strong><p>{fmt(v)} reviews</p></div>}/>}/>
          <Bar dataKey="reviews" fill="var(--color-reviews)" isAnimationActive={false}/>
        </BarChart>
      </ChartContainer></div>
    <div><p className="chart-axis-label">Average VADER sentiment, per {per}</p>
      <ChartContainer config={{sentiment:{label:`ZIP ${zip}`,color:'#245c49'},metro_sentiment:{label:`Rest of ${cityLabel}`,color:'#889686'}}} className="decision-chart" style={{height:170}} aria-label={`ZIP ${zip}: sentiment compared with the rest of the city`}>
        <LineChart data={series} margin={{top:5,right:8,left:0,bottom:0}}>
          <CartesianGrid vertical={false}/>{x}<YAxis width={44} domain={['auto','auto']} tickLine={false} axisLine={false} fontSize={10} tickFormatter={(v:number)=>fmt(v,2)}/>
          {marks}
          <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(v:any,name:any,item:any)=><div className="chart-tooltip-row"><span style={{color:item.color}}>{name==='sentiment'?`ZIP ${zip}`:'Rest of city'} · {item.payload.label}</span><strong>{fmt(v,3)}</strong></div>}/>}/>
          <ChartLegend content={<ChartLegendContent/>}/>
          <Line dataKey="metro_sentiment" stroke="var(--color-metro_sentiment)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false}/>
          <Line dataKey="sentiment" stroke="var(--color-sentiment)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false}/>
        </LineChart>
      </ChartContainer>
      <p className="chart-note text-muted-foreground">Gaps mean too few reviews in that period to score.</p></div>
  </div>;
}
