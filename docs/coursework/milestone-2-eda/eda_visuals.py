"""Publication-style figures for the five-project EDA; only aggregate inputs are used."""
from pathlib import Path
import textwrap,json
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch,Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
ORDER=['Lafitte','Sun Link','Dilworth Park','Water Works Park','Riverfront / Ascend']
NAMES=['Lafitte Greenway','Sun Link','Dilworth Park','Water Works Park','Riverfront / Ascend']
INK='#20334A';TEAL='#187D8D';ORANGE='#BD623C';GOLD='#D6A744';GRAY='#95A1AC';PALE='#E9EDF0'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.dpi':140,'savefig.dpi':180,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#B8C0C8','axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,'axes.titleweight':'bold','axes.titlesize':11,'figure.facecolor':'white','axes.facecolor':'white'})
def finish(fig,out,name):
 out=Path(out);out.mkdir(exist_ok=True);fig.savefig(out/(name+'.png'),bbox_inches='tight',facecolor='white');fig.savefig(out/(name+'.svg'),bbox_inches='tight',facecolor='white');return fig
def title(fig,headline,subtitle):
 fig.suptitle(headline,x=.02,y=.99,ha='left',fontsize=18,fontweight='bold');fig.text(.02,.90,subtitle,fontsize=10,color='#596876',va='top')
def study_design(reg,out):
 fig,ax=plt.subplots(figsize=(12.7,5.2));fig.subplots_adjust(left=.21,right=.82,top=.78,bottom=.17)
 types=['Greenway / public space','Streetcar / transit','Civic plaza / transit access','Park / spring restoration','Park / performance venue']
 for i,p in enumerate(ORDER):
  r=reg.set_index('project').loc[p];pre=r['pre'];post=r['post'];opening=pd.Timestamp(r.opening);year=opening.year+(opening.dayofyear-1)/365.25
  ax.broken_barh([(pre[0],2)],(i-.14,.28),facecolors=GRAY);ax.broken_barh([(max(pre)+1,min(post)-max(pre)-1)],(i-.14,.28),facecolors=PALE);ax.broken_barh([(post[0],2)],(i-.14,.28),facecolors=TEAL)
  ax.scatter(year,i,marker='D',s=35,color=GOLD,zorder=3);ax.text(2018.38,i-.07,f'${r.cost_millions:g}m',fontsize=12,fontweight='bold',va='center');ax.text(2018.38,i+.18,types[i],fontsize=8.5,va='center',color='#596876')
 ax.set(yticks=range(5),yticklabels=[f'{NAMES[i]}\n{reg.set_index("project").loc[p,"city"]}' for i,p in enumerate(ORDER)],xlim=(2009.8,2018.1),ylim=(4.6,-.6),xticks=range(2010,2019),xlabel='Calendar year');ax.grid(axis='x',color=PALE);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0,pad=12)
 title(fig,'Project characteristics and observation windows','Each case has two baseline and two follow-up years. Construction and opening gaps are excluded.')
 fig.text(.835,.825,'REPORTED COST / TYPE',fontsize=9,fontweight='bold')
 fig.legend(handles=[Patch(color=GRAY,label='Before construction'),Patch(color=PALE,label='Excluded gap'),Line2D([],[],marker='D',linestyle='',color=GOLD,label='Opening'),Patch(color=TEAL,label='Post-opening')],loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.47,.01),fontsize=9)
 return finish(fig,out,'01_study_design')
def coverage(overview,quality,support,out):
 z=overview.set_index('project').loc[ORDER].join(quality.set_index('project')[['baseline_near_500']]).join(support.query("radius_m==500 and income_group=='All'").set_index('project')[['matched_pairs']]);fig,ax=plt.subplots(figsize=(12,4.7));fig.subplots_adjust(left=.20,right=.78,top=.77,bottom=.15)
 y=np.arange(5);ax.barh(y,100,color=PALE,height=.6);ax.barh(y,100*z.baseline_near_500/z.listed_500m,color=GOLD,height=.6);ax.barh(y,100*z.matched_pairs/z.listed_500m,color=TEAL,height=.6)
 for i,p in enumerate(ORDER):ax.text(103,i,f'{int(z.loc[p,"matched_pairs"]):,} / {int(z.loc[p,"listed_500m"]):,}',va='center',fontsize=11,fontweight='bold',color=ORANGE if p=='Water Works Park' else INK)
 ax.set(yticks=y,yticklabels=NAMES,xlim=(0,100),ylim=(4.6,-.6),xticks=[0,25,50,75,100],xlabel='Share of nearby listings (%)');ax.tick_params(axis='y',length=0);title(fig,'Business coverage and matched samples','Four cases support the primary comparison. Water Works has only two matched businesses.')
 fig.text(.80,.81,'MATCHED / LISTED',fontsize=9,fontweight='bold');fig.legend(handles=[Patch(color=TEAL,label='Matched'),Patch(color=GOLD,label='Baseline ≥5, unmatched'),Patch(color=PALE,label='Fewer than 5 baseline reviews')],loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.52,-.02),fontsize=9)
 return finish(fig,out,'02_coverage')
def text_diagnostics(cm,length,out):
 fig,axes=plt.subplots(1,2,figsize=(12.8,5.1),gridspec_kw={'width_ratios':[1,1.3]});fig.subplots_adjust(left=.09,right=.96,bottom=.19,top=.75,wspace=.65)
 z=cm.groupby(['stars','vader_label']).reviews.sum().unstack(fill_value=0).reindex(index=[1,2,3,4,5],columns=['Negative','Neutral','Positive']);pct=100*z.div(z.sum(axis=1),axis=0);ax=axes[0];ax.imshow(pct,cmap='Blues',vmin=0,vmax=100,aspect='auto')
 for i in range(5):
  for j in range(3):ax.text(j,i,f'{pct.iloc[i,j]:.1f}%',ha='center',va='center',color='white' if pct.iloc[i,j]>60 else INK,fontweight='bold')
 ax.set(xticks=range(3),xticklabels=pct.columns,yticks=range(5),yticklabels=[f'{i} star'+('' if i==1 else 's') for i in range(1,6)],title='VADER labels within each star rating',xlabel='Whole-review sentiment label');ax.tick_params(length=0)
 ax=axes[1];z=length.set_index('project').loc[ORDER];y=np.arange(5);ax.hlines(y,z.p10_words,z.p90_words,color=GRAY,lw=3);ax.scatter(z.median_words,y,color=TEAL,s=50,zorder=3)
 for i,row in enumerate(z.itertuples()):ax.text(row.p90_words+7,i,str(int(row.median_words))+' median',va='center',fontsize=9)
 ax.set(yticks=y,yticklabels=NAMES,ylim=(4.5,-.5),xlim=(0,340),title='Review length by project',xlabel='Words per review');ax.tick_params(axis='y',length=0);ax.grid(axis='x',color=PALE)
 title(fig,'VADER sentiment and review length','All pre/post review text within 500 m. Star labels provide an imperfect check on VADER sentiment.')
 fig.text(.57,.04,'Line: 10th–90th percentile   •   Dot: median',fontsize=9,color='#596876')
 return finish(fig,out,'03_text_diagnostics')
def outcome_panel(activity,experience,out):
 fig,axes=plt.subplots(1,5,figsize=(15.3,5.2));fig.subplots_adjust(left=.16,right=.985,top=.73,bottom=.16,wspace=.25)
 specs=[('reviews','Review activity','Relative growth (%)',(-55,165)),('checkins','Check-ins','Relative growth (%)',(-55,190)),('tips','Tips','Relative growth (%)',(-60,180)),('stars','Stars','Change contrast (stars)',(-.13,.08)),('compound','VADER','Change contrast (compound)',(-.075,.06))]
 for ax,(metric,heading,xlabel,limits) in zip(axes,specs):
  z=activity.query("radius_m==500 and income_group=='All' and window=='Main'") if metric in ['reviews','checkins','tips'] else experience.query("radius_m==500 and income_group=='All'");z=z[z.metric.eq(metric)].set_index('project').reindex(ORDER);vcol='relative_growth_pct' if metric in ['reviews','checkins','tips'] else 'contrast'
  for i,p in enumerate(ORDER):
   val=z.at[p,vcol];n=z.at[p,'pairs']
   if n<20:ax.axhspan(i-.35,i+.35,color='#F3F4F5');ax.text(sum(limits)/2,i,'Sparse: n=2',ha='center',va='center',fontsize=8,color='#77828C');continue
   color=TEAL if val>=0 else ORANGE;ax.hlines(i,0,val,color=color,lw=2);ax.scatter(val,i,s=48,color=color,zorder=3);label=f'{val:+.1f}' if metric in ['reviews','checkins','tips'] else f'{val:+.3f}';ax.annotate(label,(val,i),xytext=(5 if val>=0 else -5,0),textcoords='offset points',ha='left' if val>=0 else 'right',va='center',fontsize=8)
  ax.axvline(0,color='#9AA5AF',lw=.8);ax.set(xlim=limits,ylim=(4.6,-.6),yticks=range(5),yticklabels=NAMES if ax==axes[0] else [],title=heading,xlabel=xlabel);ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=8);ax.xaxis.set_major_locator(plt.MaxNLocator(3));ax.grid(axis='y',color=PALE,zorder=0)
 title(fig,'Matched changes in engagement and review experience','Matched businesses within 500 m versus farther controls. Positive values favor nearby businesses. The estimates are descriptive.')
 fig.text(.16,.025,'Activity cohorts: 142 / 149 / 498 / 2 / 85 pairs.   Experience cohorts: 59 / 75 / 248 / 2 / 45 pairs, in project order.',fontsize=9,color='#596876')
 return finish(fig,out,'04_outcomes')
def income_panel(activity,support,out):
 fig,ax=plt.subplots(figsize=(11,5));fig.subplots_adjust(left=.24,right=.9,top=.75,bottom=.15);groups=['Lower','Middle','Higher'];z=activity.query("radius_m==500 and metric=='reviews' and window=='Main' and income_group!='All'").pivot(index='project',columns='income_group',values='relative_growth_pct').reindex(index=ORDER,columns=groups);n=support.query("radius_m==500 and income_group!='All'").pivot(index='project',columns='income_group',values='matched_pairs').reindex(index=ORDER,columns=groups);masked=z.mask(n<20)
 im=ax.imshow(masked,cmap='BrBG',norm=TwoSlopeNorm(vmin=-200,vcenter=0,vmax=200),aspect='auto')
 for i in range(5):
  for j in range(3):
   count=int(n.iloc[i,j]);value=z.iloc[i,j]
   if count<20:ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor='#EEF0F2',edgecolor='white'));text='No pairs' if count==0 else f'Sparse\nn={count}';color='#78838E'
   else:text=f'{value:+.1f}%\nn={count}';color='white' if abs(value)>130 else INK
   ax.text(j,i,text,ha='center',va='center',color=color,fontsize=10)
 ax.set(xticks=range(3),xticklabels=['Lower local ZIP income','Middle local ZIP income','Higher local ZIP income'],yticks=range(5),yticklabels=NAMES);ax.tick_params(length=0);fig.colorbar(im,ax=ax,fraction=.045,pad=.025,label='Relative review growth (%)',ticks=[-200,-100,0,100,200]);title(fig,'Relative review growth by neighborhood income','Baseline ACS income at the business ZIP. Each city has its own income bands. Reviewer incomes are unknown.')
 return finish(fig,out,'05_income')
def sensitivity(activity,influence,out):
 fig,axes=plt.subplots(1,5,figsize=(14,4.5),sharey=True);fig.subplots_adjust(left=.07,right=.98,top=.73,bottom=.18,wspace=.20)
 z=activity.query("income_group=='All' and metric=='reviews' and window=='Main'")
 for ax,p,name in zip(axes,ORDER,NAMES):
  q=z[z.project.eq(p)].sort_values('radius_m');q=q.copy();q.loc[q.pairs<20,'relative_growth_pct']=np.nan;ax.plot(q.radius_m,q.relative_growth_pct,color=GRAY,lw=1.8,marker='o',markersize=5)
  primary=q[q.radius_m.eq(500)]
  if primary.pairs.iloc[0]>=20:ax.scatter(500,primary.relative_growth_pct.iloc[0],color=TEAL,s=65,zorder=3)
  else:ax.text(.5,.8,'250 m / 500 m\nsamples too small',transform=ax.transAxes,ha='center',fontsize=9,color='#75828E')
  ax.axhline(0,color='#A7B0B8',lw=.8);ax.set(title=name,xticks=[250,500,1000],xlim=(175,1075),ylim=(-65,190),xlabel='Radius (m)');ax.tick_params(axis='x',labelsize=9);ax.grid(axis='y',color=PALE)
 axes[0].set_ylabel('Relative review growth (%)');title(fig,'Relative review growth by distance from project','Dots compare 250 m, 500 m and 1,000 m definitions. Teal marks the primary estimate. These are sensitivity checks.')
 return finish(fig,out,'06_sensitivity')
def topic_panel(topics,out):
 cats=['Food and dishes','Location/local identity (mixed)','Mixed evaluations/negation','Mixed interactions/intentions','Overall experience/service','Visit timing/waiting'];short=['Food /\ndishes','Local\nidentity\n(mixed)','Evaluation\n/ negation\n(mixed)','Interaction\n/ intention\n(mixed)','Experience\n/ service','Visit timing\n/ waiting']
 fig,axes=plt.subplots(1,2,figsize=(14,5.2));fig.subplots_adjust(left=.15,right=.98,top=.72,bottom=.23,wspace=.23)
 for ax,metric,heading,limit in zip(axes,['vader','stars'],['Category sentence sentiment','Associated whole-review stars'],[.10,.35]):
  z=topics[topics.area.eq('near')].pivot(index='project',columns=['period','category'],values=metric);delta=(z['post']-z['pre']).reindex(index=ORDER,columns=cats);im=ax.imshow(delta,cmap='BrBG',norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),aspect='auto')
  for i in range(5):
   for j in range(6):
    v=delta.iloc[i,j]
    if pd.isna(v):ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor='#EEF0F2',edgecolor='white'));label='—';color='#86909B'
    else:label=f'{v:+.2f}';color='white' if abs(v)>.65*limit else INK
    ax.text(j,i,label,ha='center',va='center',fontsize=8,color=color)
  ax.set(xticks=range(6),xticklabels=short,yticks=range(5),yticklabels=NAMES if ax==axes[0] else [],title=heading);ax.tick_params(length=0,labelsize=8);fig.colorbar(im,ax=ax,fraction=.035,pad=.025,shrink=.75)
 title(fig,'Sentiment and ratings by review category','Post minus pre means for sampled nearby reviews. Business mix may explain differences. Gray cells lack 30 reviews in a period.')
 fig.text(.15,.07,'A review can discuss several categories. Sentence sentiment and whole-review stars measure different things.\nThe model uses the original two cities\' baseline text. We freeze it for all five cases.',fontsize=9,color='#596876')
 return finish(fig,out,'07_topics')
def sun_panel(composition,scopes,out):
 fig,axes=plt.subplots(1,2,figsize=(12.8,5.2),gridspec_kw={'width_ratios':[1,1.25]});fig.subplots_adjust(left=.08,right=.97,top=.74,bottom=.22,wspace=.6)
 ax=axes[0];bottom=np.zeros(2);colors=[INK,GRAY,GOLD];groups=['5+ baseline reviews','1–4 baseline reviews','No baseline reviews'];labels=['5+ baseline reviews','1–4 baseline reviews','No baseline reviews']
 for group,color,label in zip(groups,colors,labels):
  z=composition.set_index('baseline_group').loc[group];v=np.array([z.baseline_reviews,z.post_reviews]);ax.bar([0,1],v,bottom=bottom,width=.55,color=color,label=label)
  if group=='No baseline reviews':ax.text(1,bottom[1]+v[1]/2,'49.4%\nof post reviews',ha='center',va='center',color=INK,fontweight='bold',fontsize=10)
  bottom+=v
 for i,v in enumerate(bottom):ax.text(i,v+250,f'{int(v):,}',ha='center',fontweight='bold')
 ax.set(xticks=[0,1],xticklabels=['2010–11\nBaseline','2015–16\nPost-opening'],ylabel='Recorded corridor reviews',ylim=(0,12500),title='Review counts by baseline activity');ax.legend(loc='upper left',bbox_to_anchor=(-.12,-.18),ncol=1,frameon=False,fontsize=9)
 ax=axes[1];z=scopes.query("radius_m==500 and scope=='All listed businesses' and period=='post'").set_index('metric');metrics=['reviews','checkins','tips'];vals=z.loc[metrics,'relative_growth_pct']
 for i,(metric,val) in enumerate(vals.items()):
  color=TEAL if val>=0 else ORANGE;ax.hlines(i,0,val,color=color,lw=3);ax.scatter(val,i,color=color,s=60);ax.annotate(f'{val:+.1f}%',(val,i),xytext=(7 if val>=0 else -7,0),textcoords='offset points',ha='left' if val>=0 else 'right',va='center',fontsize=11,fontweight='bold')
 ax.axvline(0,color='#A7B0B8');ax.set(yticks=[0,1,2],yticklabels=['Reviews','Check-ins','Tips'],ylim=(2.6,-.6),xlim=(-48,15),xlabel='Relative growth versus farther area (%)',title='Relative growth by engagement measure');ax.tick_params(axis='y',length=0);title(fig,'Sun Link corridor engagement and business composition','All 717 Yelp listings within 500 m of the route. This unmatched comparison includes listings with no baseline reviews.')
 return finish(fig,out,'08_sun_corridor')

def draw_geometry(ax, geometry, facecolor, edgecolor, linewidth=1, alpha=1):
 from matplotlib.path import Path as PlotPath
 from matplotlib.patches import PathPatch
 kind=geometry['type'];coords=geometry['coordinates']
 if kind=='Polygon':
  paths=[]
  for ring in coords:
   points=np.asarray(ring)
   codes=[PlotPath.MOVETO]+[PlotPath.LINETO]*(len(points)-2)+[PlotPath.CLOSEPOLY]
   paths.append(PlotPath(points,codes))
  ax.add_patch(PathPatch(PlotPath.make_compound_path(*paths),facecolor=facecolor,edgecolor=edgecolor,lw=linewidth,alpha=alpha))
 elif kind in ['MultiPolygon','MultiLineString']:
  for part in coords:draw_geometry(ax,{'type':'Polygon' if kind=='MultiPolygon' else 'LineString','coordinates':part},facecolor,edgecolor,linewidth,alpha)
 elif kind=='LineString':
  points=np.asarray(coords);ax.plot(points[:,0],points[:,1],color=edgecolor,lw=linewidth,alpha=alpha)

def project_location_map(cartography,out):
 fig=plt.figure(figsize=(14,9.1))
 title(fig,'Project locations and nearby study areas','Five US projects. Local panels show the mapped footprint and the primary 500 m study buffer.')
 ax=fig.add_axes([.035,.40,.66,.46]);ax.set_aspect('equal');ax.set_axis_off()
 selected={'Louisiana','Arizona','Pennsylvania','Florida','Tennessee'}
 for state in cartography['states']:
  draw_geometry(ax,state['geometry'],'#DCEBED' if state['name'] in selected else '#EEF1F3','white',.75)
 ax.set_xlim(-2500000,2400000);ax.set_ylim(100000,3300000)
 offsets=[(-45,-27),(-12,-26),(12,16),(25,-4),(-15,26)]
 for i,(p,offset) in enumerate(zip(cartography['projects'],offsets)):
  x,y=p['national_xy'];ax.scatter(x,y,s=170,facecolor=TEAL,edgecolor='white',lw=1.5,zorder=5)
  ax.text(x,y,str(i+1),ha='center',va='center',fontsize=8,color='white',fontweight='bold',zorder=6)
  ax.annotate(p['city'],(x,y),xytext=offset,textcoords='offset points',ha='center' if i!=2 else 'left',fontsize=10,color=INK,arrowprops={'arrowstyle':'-','color':GRAY,'lw':.7},bbox={'boxstyle':'round,pad=.2','fc':'white','ec':'none','alpha':.9},zorder=4)
 fig.text(.735,.825,'Projects',fontsize=13,fontweight='bold')
 for i,p in enumerate(cartography['projects']):
  y=.775-i*.063
  fig.text(.735,y,str(i+1),ha='center',va='center',fontsize=10,color='white',fontweight='bold',bbox={'boxstyle':'circle,pad=.35','fc':TEAL,'ec':'none'})
  fig.text(.76,y+.008,NAMES[i],fontsize=10,fontweight='bold',va='center')
  fig.text(.76,y-.017,p['city'],fontsize=9,color='#596876',va='center')
 fig.text(.035,.37,'Local project footprints',fontsize=13,fontweight='bold')
 fig.text(.035,.34,'Common scale across panels. Grid north is up. Buffers use local UTM projections.',fontsize=9,color='#596876')
 for i,p in enumerate(cartography['projects']):
  a=fig.add_axes([.035+i*.195,.09,.18,.22]);a.set_aspect('equal');a.set_facecolor('#F7F9FA')
  draw_geometry(a,p['near_buffer'],'#DCEBED','#A2C6CC',.65)
  draw_geometry(a,p['footprint'],TEAL,TEAL,1.3)
  a.set(xlim=(-4,4),ylim=(-4,4),xticks=[],yticks=[])
  for spine in a.spines.values():spine.set_visible(True);spine.set_edgecolor('#E3E8EC')
  a.set_title(f'{i+1}  {NAMES[i]}',fontsize=9,loc='left',pad=9)
  a.plot([-3.3,-2.3],[-3.3,-3.3],color=INK,lw=2);a.text(-2.8,-2.95,'1 km',ha='center',fontsize=7)
 fig.legend(handles=[Patch(facecolor=TEAL,label='Mapped project footprint'),Patch(facecolor='#DCEBED',edgecolor='#A2C6CC',label='Within 500 m of footprint')],loc='lower left',bbox_to_anchor=(.03,.025),ncol=2,frameon=False,fontsize=9)
 fig.text(.985,.045,'State boundaries: Natural Earth 1:110m',ha='right',fontsize=8,color='#596876')
 return finish(fig,out,'00_project_map')

def business_growth_panel(growth,out):
 fig,axes=plt.subplots(1,2,figsize=(13.6,5.4),gridspec_kw={'width_ratios':[1.25,1]})
 fig.subplots_adjust(left=.18,right=.96,top=.74,bottom=.18,wspace=.42)
 near=growth[growth.area.eq('Near')].set_index('project').loc[ORDER]
 ax=axes[0]
 for i,row in enumerate(near.itertuples()):
  ax.plot([row.baseline_active,row.post_active],[i,i],color='#CDD6DC',lw=3)
  ax.scatter(row.baseline_active,i,color=GRAY,s=45,zorder=3);ax.scatter(row.post_active,i,color=TEAL,s=55,zorder=3)
  ax.annotate(f'{row.baseline_active:,}',(row.baseline_active,i),xytext=(-6,9),textcoords='offset points',ha='right',fontsize=9,color='#596876')
  ax.annotate(f'{row.post_active:,}',(row.post_active,i),xytext=(6,-13),textcoords='offset points',ha='left',fontsize=9,color=TEAL,fontweight='bold')
 ax.set(yticks=range(5),yticklabels=NAMES,ylim=(4.6,-.6),xlim=(-25,1280),xlabel='Businesses with at least one review',title='Nearby reviewed businesses');ax.tick_params(axis='y',length=0);ax.grid(axis='x',color=PALE)
 ax.legend(handles=[Line2D([],[],marker='o',ls='',color=GRAY,label='Baseline'),Line2D([],[],marker='o',ls='',color=TEAL,label='Post-opening')],frameon=False,ncol=2,loc='upper left',bbox_to_anchor=(0,-.16),fontsize=9)
 ax=axes[1]
 for i,row in enumerate(near.itertuples()):
  if row.baseline_active<20:
   ax.axhspan(i-.33,i+.33,color='#F1F3F5');ax.text(-9,i,'Small baseline: 6 businesses',ha='center',va='center',fontsize=9,color='#75828E');continue
  v=row.relative_growth_pct;color=TEAL if v>=0 else ORANGE
  ax.hlines(i,0,v,color=color,lw=2);ax.scatter(v,i,s=55,color=color)
  ax.annotate(f'{v:+.1f}%',(v,i),xytext=(7 if v>=0 else -7,0),textcoords='offset points',ha='left' if v>=0 else 'right',va='center',fontsize=10,fontweight='bold',color=color)
 ax.axvline(0,color=GRAY,lw=.8);ax.set(yticks=range(5),yticklabels=[],ylim=(4.6,-.6),xlim=(-29,13),xticks=[-20,-10,0,10],xlabel='Relative growth versus farther area (%)',title='Growth in reviewed-business counts');ax.tick_params(axis='y',length=0);ax.grid(axis='y',color=PALE)
 title(fig,'Business activity around each project','Nearby: within 500 m. Farther: more than 1.5 km and up to 8 km. These area comparisons are unmatched.')
 fig.text(.18,.025,'A first or last review does not establish a business opening or closure. Counts use equal two-year windows.',fontsize=9,color='#596876')
 return finish(fig,out,'09_business_growth')
