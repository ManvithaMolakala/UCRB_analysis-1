import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.patches
from scipy import stats
import itertools
import seaborn as sns

sns.set_style("white")

designs = ['LHsamples_original_1000_AnnQonly','CMIPunscaled_SOWs','Paleo_SOWs','LHsamples_wider_1000_AnnQonly']
nsamples = [1000,97,366,1000]
titles = ['Box Around Historical','CMIP','Paleo','All-Encompassing']
structures = ['53_ADC022','7200645']
nrealizations = 10
idx = np.arange(2,22,2)

def alpha(i, base=0.2):
    l = lambda x: x+base-x*base
    ar = [l(0)]
    for j in range(i):
        ar.append(l(ar[-1]))
    return ar[-1]

def shortage_duration(sequence):
    cnt_shrt = [sequence[i]>0 for i in range(len(sequence))] # Returns a list of True values when there's a shortage
    shrt_dur = [ sum( 1 for _ in group ) for key, group in itertools.groupby( cnt_shrt ) if key ] # Counts groups of True values
    return shrt_dur
  
def plotSDC(ax, synthetic, histData, nsamples):
    n = 12 # number of months
    #Reshape historic data to a [no. years x no. months] matrix
    f_hist = np.reshape(histData, (int(np.size(histData)/n), n))
    #Reshape to annual totals
    f_hist_totals = np.sum(f_hist,1)  
    #Calculate historical shortage duration curves
    F_hist = np.sort(f_hist_totals) # for inverse sorting add this at the end [::-1]
    
    #Reshape synthetic data
    #Create matrix of [no. years x no. months x no. samples]
    synthetic_global = np.zeros([int(np.size(histData)/n),n,nsamples*nrealizations]) 
    # Loop through every SOW and reshape to [no. years x no. months]
    for j in range(nsamples*nrealizations):
        synthetic_global[:,:,j]= np.reshape(synthetic[:,j], (int(np.size(synthetic[:,j])/n), n))
    #Reshape to annual totals
    synthetic_global_totals = np.sum(synthetic_global,1) 
    
    p=np.arange(100,-10,-10)
    
    #Calculate synthetic shortage duration curves
    F_syn = np.empty([int(np.size(histData)/n),nsamples])
    F_syn[:] = np.NaN
    for j in range(nsamples):
        F_syn[:,j] = np.sort(synthetic_global_totals[:,j])
    
    # For each percentile of magnitude, calculate the percentile among the experiments ran
    perc_scores = np.zeros_like(F_syn) 
    for m in range(int(np.size(histData)/n)):
        perc_scores[m,:] = [stats.percentileofscore(F_syn[m,:], j, 'rank') for j in F_syn[m,:]]
                
    P = np.arange(1.,len(F_hist)+1)*100 / len(F_hist)
    
    handles = []
    labels=[]
    color = '#000292'
    for i in range(len(p)):
        ax.fill_between(P, np.min(F_syn[:,:],1), np.percentile(F_syn[:,:], p[i], axis=1), color=color, alpha = 0.1)
        ax.plot(P, np.percentile(F_syn[:,:], p[i], axis=1), linewidth=0.5, color=color, alpha = 0.3)
        handle = matplotlib.patches.Rectangle((0,0),1,1, color=color, alpha=alpha(i, base=0.1))
        handles.append(handle)
        label = "{:.0f} %".format(100-p[i])
        labels.append(label)
    ax.plot(P,F_hist, c='black', linewidth=2, label='Historical record')
    ax.set_xlim(0,100)
    
    return handles, labels

fig = plt.figure()
count = 1 # subplot counter
for structure in structures:
    # load historical shortage data
    histData = np.loadtxt('../Simulation_outputs/' + structure + '_info_hist.txt')[:,2]
    # replace failed runs with np.nan (currently -999.9)
    histData[histData < 0] = np.nan
    for i, design in enumerate(designs):
        # load shortage data for this experimental design
        synthetic = np.load('../../../Simulation_outputs/' + design + '/' + structure + '_info.npy')
        # remove columns for year (0) and demand (odd columns)
        synthetic = synthetic[:,idx,:]
        # reshape into 12*nyears x nsamples*nrealizations
        synthetic = synthetic.reshape([np.shape(synthetic)[0],np.shape(synthetic)[1]*np.shape(synthetic)[2]])
        # replace failed runs with np.nan (currently -999.9)
        synthetic[synthetic < 0] = np.nan
        
        # plot shortage distribution
        ax = fig.add_subplot(2,4,count)
        handles, labels = plotSDC(ax, synthetic, histData, nsamples[i])
        
        # only put labels on bottom row/left column, make y ranges consistent, title experiment
        if count == 1 or count == 5:
            ax.tick_params(axis='y', labelsize=14)
        else:
            ax.tick_params(axis='y',labelleft='off')
            
        if count <= 4:
            ax.tick_params(axis='x',labelbottom='off')
            ax.set_title(titles[count-1],fontsize=16)
            ax.set_ylim(0,5000)
        else:
            ax.tick_params(axis='x',labelsize=14)
            ax.set_ylim(0,260000)
            
        # iterature subplot counter
        count += 1
        
fig.set_size_inches([16,8])
fig.text(0.5, 0.15, 'Percentile', ha='center', fontsize=16)
fig.text(0.05, 0.5, 'Annual Shortage (m' + r'$^3$' + ')', va='center', rotation=90, fontsize=16)
fig.subplots_adjust(bottom=0.22)
labels_transposed = [labels[0],labels[6],labels[1],labels[7],labels[2],labels[8],labels[3],labels[9],labels[4],labels[10],labels[5]]
handles_transposed = [handles[0],handles[6],handles[1],handles[7],handles[2],handles[8],handles[3],handles[9],handles[4],handles[10],handles[5]]
legend = fig.legend(handles=handles_transposed, labels=labels_transposed, fontsize=16, loc='lower center', title='Frequency in experiment', ncol=6)
plt.setp(legend.get_title(),fontsize=16)
fig.savefig('Figure6_ShortageDistns.pdf')
fig.clf()