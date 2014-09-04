import subprocess
import os.path

def get_filenames(folder,confusibles):
	
	confst = ','.join(confusibles);
	traindata = {};
	testdata = {}

	for goaldict, infix in [(traindata,'train'),(testdata,'test')]:
	
		for variant in variants:

			goaldict[variant] = folder + '/' + confst + '.' + variant + '.' + infix + '.inst';

	return traindata, testdata;

def command(command):   
    command = command.split(' ');
 
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      print(line.strip());
      if(retcode is not None):
        break

def parse_distribution(distrstr):
	
	distribution = {};

	plain_distr = ' '.join(distrstr).replace('{','').replace('}','').strip();
	neighbours = plain_distr.split(',');

	for neighbour in neighbours:

		cl,freq = neighbour.strip().split(' ');
	
		distribution[cl] = float(freq);

	return distribution;

def create_model(filepath,modeldir):

	filename = filepath.split('/')[1];
	output = modeldir+'/'+filename.replace('inst','IGTree');

	if not(os.path.isfile(output)) or not(skip_train):
		command('timbl -f '+filepath+' -a1 +D +vdb -I '+output);
	else:
		print('Skipped model creation');

	return output;

def test_model(filepath,modelpath,outputdir):

	filename = filepath.split('/')[1];
	output = outputdir+'/'+filename+'.out';

	if not(os.path.isfile(output)) or not(skip_test):
		command('timbl -t '+filepath+' -i '+modelpath+' -a1 +D +vdb -o '+output);
	else:
		print('Skipped TiMBL testing');

	return output

def analyze_data(outputpath,nr_features):

	#First set up the three-dimensional array to store the results
	confusion_matrices = {};
	for threshold in thresholds:

		confusion_matrices[threshold] = {'positive':{True:0,False:0},'negative':{True:0,False:0}};

	#Go through to file and store the results in right part of the array
	for n,line in enumerate(open(outputpath)):

		if n%(1/error_ratio) == 0:
			error = True; 
			no_error = False;
		else:
			error = False;
			no_error = True

		for threshold in thresholds:

			words = line.split();	
			distr = parse_distribution(words[nr_features+2:]);
			confidence = max(distr.values()) / sum(distr.values());
		
			if words[nr_features] == words[nr_features+1] or confidence < threshold:
				confusion_matrices[threshold]['negative'][no_error] += 1;
			else:
				confusion_matrices[threshold]['positive'][error] += 1;

	print confusion_matrices;

#=================================
# Script starts here
#=================================

if __name__ == '__main__':

	#Parameters
	variants = ['noclass','withclass','err'];
	nr_features = [6,7,7];
	classes = ['than','then'];
	thresholds = [0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.96,0.97,0.98,0.99];

	inputfolder = 'manipulated_data';
	modelfolder = 'temp_models';
	outputfolder = 'results';
	skip_train = True;
	skip_test = True;

	traindata, testdata = get_filenames(inputfolder,classes);

	error_ratio = 0.1;

	#For each variant, experiment
	for n,variant in enumerate(variants):

		#Do the actual experiments
		print('Creating model for ',variant);
		modelpath = create_model(traindata[variant],modelfolder);

		print('Testing model for ',variant);
		outputpath = test_model(testdata[variant],modelpath,outputfolder);

		#Analyse the results
		print('Analyzing ',variant);
		analyze_data(outputpath,nr_features[n]);
