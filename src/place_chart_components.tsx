import * as React from 'react';
import {createRoot, type Root} from 'react-dom/client';
import {Line,LineChart,Bar,BarChart,CartesianGrid,XAxis,YAxis,ReferenceLine,Cell,Scatter,ScatterChart,ErrorBar} from 'recharts';
import {ChartContainer,ChartTooltip,ChartTooltipContent,ChartLegend,ChartLegendContent} from './components/ui/chart';
const roots=new Map<string,Root>();
export function clearChart(id:string,message:string) {
  roots.get(id)?.unmount();roots.delete(id);
  document.getElementById(id)!.textContent=message;
}
function mount(id:string,element:React.ReactNode,tableHTML:string) {
  const node=document.getElementById(id)!;
  let root=roots.get(id);if(!root){node.replaceChildren();root=createRoot(node);roots.set(id,root);}
  root.render(<>{element}<div dangerouslySetInnerHTML={{__html:tableHTML}}/></>);
}
export function mountLineChart(id:string,options:any,tableHTML:string) {
  const {title,series,xLabel,yLabel,xFormat,yFormat,opening,endpoint}=options;
  const config=Object.fromEntries(series.map((s:any,i:number)=>['s'+i,{label:s.label,color:s.color}]));
  const xs=[...new Set<number>(series.flatMap((s:any)=>s.points.map((p:any)=>p.x)))].sort((a,b)=>a-b);
  const data=xs.map(x=>Object.assign({x},...series.map((s:any,i:number)=>({['s'+i]:s.points.find((p:any)=>p.x===x)?.y??null}))));
  const ys=series.flatMap((s:any)=>s.points.map((p:any)=>p.y)).filter(Number.isFinite);
  const domain=[Math.min(0,...ys,endpoint?.low??0),Math.max(0,...ys,endpoint?.high??0)];
  const pad=Math.max(1,(domain[1]-domain[0])*.12);
  // Sparse historical series retain their own observations; fits are separate datasets.
  mount(id,<><p className="chart-axis-label">{yLabel}</p><ChartContainer config={config} className="decision-chart" aria-label={title}>
    <LineChart accessibilityLayer data={data} margin={{top:12,right:30,left:5,bottom:8}}>
      <CartesianGrid vertical={false}/><XAxis type="number" dataKey="x" domain={['dataMin','dataMax']} tickFormatter={xFormat} axisLine={false} tickLine={false} minTickGap={30}/>
      <YAxis domain={[domain[0]-pad,domain[1]+pad]} tickFormatter={yFormat} axisLine={false} tickLine={false} width={65}/>
      <ReferenceLine y={0} stroke="#b4c2ae"/>
      {opening!=null&&<ReferenceLine x={opening} stroke="#b56b32" strokeDasharray="4 5" label={{value:'Opening',position:'insideTopRight',fill:'#b56b32',fontSize:11}}/>}
      <ChartTooltip content={<ChartTooltipContent indicator="line" labelFormatter={(_,payload:any)=>`${xLabel}: ${xFormat(payload[0]?.payload?.x)}`} formatter={(value:any,name:any,item:any)=><div className="chart-tooltip-row"><span style={{color:item.color}}>{config[name]?.label||name}</span><strong>{yFormat(value)}</strong></div>}/>}/>
      <ChartLegend content={<ChartLegendContent className="flex-wrap"/>}/>
      {series.map((s:any,i:number)=><Line key={i} data={s.points.map((p:any)=>({x:p.x,['s'+i]:p.y}))} type="linear" dataKey={'s'+i} name={'s'+i} stroke={`var(--color-s${i})`} strokeWidth={s.dashed?2:2.6} strokeDasharray={s.dashed?'6 5':undefined} connectNulls={s.dashed} dot={s.points.length<15?{r:4}:false} activeDot={{r:6}} isAnimationActive={false}/>)}
      {endpoint&&<Line data={[{x:endpoint.x,errorMid:(endpoint.low+endpoint.high)/2,error:(endpoint.high-endpoint.low)/2}]} type="linear" dataKey="errorMid" name="Historical error envelope" stroke="#b56b32" dot={false} legendType="none" tooltipType="none" isAnimationActive={false}><ErrorBar dataKey="error" width={7} strokeWidth={2} stroke="#b56b32" direction="y"/></Line>}
    </LineChart>
  </ChartContainer><p className="chart-axis-label chart-x-label">{xLabel}</p>{endpoint&&<p className="chart-range-key">Orange whisker: two-year historical error envelope · not a confidence interval</p>}</>,tableHTML);
}
export function mountBarChart(id:string,{title,rows,unit}:any,tableHTML:string) {
  const config={value:{label:unit,color:'#245c49'}};
  mount(id,<><p className="chart-axis-label">{unit}</p><ChartContainer config={config} className="decision-chart" style={{height:Math.max(290,rows.length*42)}} aria-label={title}>
    <BarChart accessibilityLayer layout="vertical" data={rows} margin={{top:10,right:40,left:10,bottom:10}}>
      <CartesianGrid horizontal={false}/><XAxis type="number" axisLine={false} tickLine={false} tickFormatter={v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:2})}/>
      <YAxis type="category" dataKey="label" axisLine={false} tickLine={false} width={155} tick={{fontSize:12}}/>
      <ReferenceLine x={0} stroke="#a8baa3"/><ChartTooltip content={<ChartTooltipContent hideLabel formatter={(value:any,_name:any,item:any)=><div><strong>{item.payload.label}</strong><p>{Number(value).toFixed(2)} {unit}</p>{item.payload.detail&&<p>{item.payload.detail}</p>}</div>}/>}/>
      <Bar dataKey="value" name="value" radius={3} maxBarSize={26} isAnimationActive={false}>{rows.map((row:any,i:number)=><Cell key={i} fill={row.color||(row.value<0?'#b56b32':'#245c49')}/>)}</Bar>
    </BarChart>
  </ChartContainer></>,tableHTML);
}
export function mountValidationChart(id:string,rows:any[],tableHTML:string) {
  const bounds=[Math.min(0,...rows.flatMap(r=>[r.observed,r.predicted]))-15,Math.max(0,...rows.flatMap(r=>[r.observed,r.predicted]))+15];
  mount(id,<><p className="chart-axis-label">City-held-out prediction · excess reviews / $1M</p><ChartContainer config={{prediction:{label:'Held-out historical project',color:'#245c49'}}} className="decision-chart" aria-label="Held-out predictions compared with observed outcomes">
    <ScatterChart accessibilityLayer margin={{top:15,right:30,left:8,bottom:10}}>
      <CartesianGrid/><XAxis type="number" dataKey="observed" domain={bounds} tickFormatter={v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:1})} tickLine={false} axisLine={false}/><YAxis type="number" dataKey="predicted" domain={bounds} tickFormatter={v=>Number(v).toLocaleString('en-US',{maximumFractionDigits:1})} tickLine={false} axisLine={false} width={65}/>
      <ReferenceLine segment={[{x:bounds[0],y:bounds[0]},{x:bounds[1],y:bounds[1]}]} stroke="#b56b32" strokeDasharray="5 5"/>
      <ReferenceLine x={0} stroke="#b4c2ae"/><ReferenceLine y={0} stroke="#b4c2ae"/>
      <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(_value:any,_name:any,item:any,index:number)=>index>0?null:<div><strong>{item.payload.project}</strong><p>Observed: {item.payload.observed.toFixed(1)}</p><p>Held-out prediction: {item.payload.predicted.toFixed(1)}</p><p>Absolute error: {Math.abs(item.payload.observed-item.payload.predicted).toFixed(1)} reviews / $1M</p></div>}/>}/>
      <Scatter name="prediction" data={rows} fill="#245c49" isAnimationActive={false}/>
    </ScatterChart>
  </ChartContainer><p className="chart-axis-label chart-x-label">Observed outcome · excess reviews / $1M</p></>,tableHTML);
}
