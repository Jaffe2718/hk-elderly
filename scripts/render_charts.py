"""Draw publication figures directly from supplied CSV values, never from PDF crops."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[1]

def render():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    distance = list(csv.DictReader((ROOT/'assets/tables/distance_binary_decisions.csv').open(encoding='utf-8-sig')))
    ages = list(csv.DictReader((ROOT/'assets/tables/age_binary_decisions.csv').open(encoding='utf-8-sig')))
    panels = [(distance,['priority_500','priority_800','priority_1000'],['500 m','800 m','1,000 m'],'Distance threshold'),(ages,['priority_main','priority_age65','priority_age75'],['60+','65+','75+'],'Age definition / 800 m')]
    fig, axs = plt.subplots(1,2,figsize=(11.5,5.8),gridspec_kw={'width_ratios':[1.1,1]})
    for ax,(rows,fields,labels,title) in zip(axs,panels):
        data=[[int(r[k]) for k in fields] for r in rows]
        ax.imshow(data,cmap=ListedColormap(['#f0f3f1','#0b776e']),vmin=0,vmax=1,aspect='auto')
        ax.set_xticks(range(3),labels);ax.set_yticks(range(len(rows)),[r['stpug_id'] for r in rows]);ax.set_title(title,loc='left',fontsize=14,pad=16,fontweight='bold')
        ax.tick_params(length=0,pad=10)
        for i,row in enumerate(data):
            for j,v in enumerate(row): ax.text(j,i,str(v),ha='center',va='center',color='white' if v else '#7a8981',fontsize=11)
        for spine in ax.spines.values(): spine.set_visible(False)
    fig.subplots_adjust(left=.09,right=.98,top=.87,bottom=.17,wspace=.43)
    fig.text(.09,.06,'1 = meets both Binary conditions   ·   0 = does not   |   Each age cohort uses its own P75 cutoff.',fontsize=10,color='#53665c')
    target=ROOT/'assets/figures/age-distance-redrawn.png'
    fig.savefig(target,dpi=180,facecolor='white');plt.close(fig)
    print('Redrawn from CSV:',target)

if __name__=='__main__':render()
