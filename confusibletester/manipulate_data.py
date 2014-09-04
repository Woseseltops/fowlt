#This script can take any input instance base, and turn it into a train/test split with and without (swapped) classnames as features

import random

class Confusible_instance():
	
	def __init__(self,cl,classes,leftcontext,rightcontext):

		self.cl = cl;
		self.classes = classes;

		self.leftcontext = leftcontext;
		self.rightcontext = rightcontext;

	def pick_other_class(self):

		while True:
			c = random.choice(self.classes);
			
			if c != self.cl.lower():
				return c;
				break;

def interpret_string(line,classes,form='class_included_errors_inserted'): 

	if form == 'class_included_errors_inserted':
		words = line.split();
		return Confusible_instance(words[-1],classes,words[:3],words[4:7]);

def get_classes(inputfile):

	classes = [];

	for line in open(inputfile):	

		c = line.split()[-1];

		if c not in classes:
			classes.append(c);

	return classes;

#=================================
# Script starts here
#=================================

if __name__ == '__main__':

	#Parameters
	classes = ['than','then'];
	testtrain_ratio = 0.1;
	trainerror_ratio = 0.1;
	testerror_ratio = 0.1;

	inputfile = 'src_data/'+','.join(classes)+'.inst';
	outputfile_prefix = 'manipulated_data/'+','.join(classes);

	#Create the various outputfiles
	output = {};

	for kind in ['noclass','withclass','err']:
	
		output[kind] = {};

		for use in ['test','train']:
			output[kind][use] = open(outputfile_prefix+'.'+kind+'.'+use+'.inst','w');

	#Go through the input file and rewrite it
	testline = 1/testtrain_ratio;
	trainerrorline = 1/trainerror_ratio;
	testerrorline = 1/testerror_ratio;

	n_train = -1
	n_test = -1;

	for n, line in enumerate(open(inputfile)):
	
		#Figure out what to use this line for (train or test),
		#and whether to put in a fake error
		insert_error = False;
	
		if n%testline == 0:
			use = 'test';
			n_test += 1;
		
			if n_test%testerrorline == 0:
				insert_error = True;

		else:
			use = 'train';
			n_train += 1;

			if n_train%trainerrorline == 0:
				insert_error = True;

		#String -> instance
		inst = interpret_string(line,classes);
	
		#Reformat
		lcontext = ' '.join(inst.leftcontext);
		rcontext = ' '.join(inst.rightcontext);

		if use == 'train': #For training, the right class is always at the end
			line_noclass = [lcontext,rcontext,inst.cl];		
			line_withclass = [lcontext,inst.cl,rcontext,inst.cl];

			if insert_error: #But there can be a wrong feature
				line_err = [lcontext,inst.pick_other_class(),rcontext,inst.cl];
			else:
				line_err = [lcontext,inst.cl,rcontext,inst.cl];

		elif use == 'test': #For testing, you don't know, so you pick what was in the
						    #material
			if insert_error:
				cl = inst.pick_other_class();
			else:
				cl = inst.cl;

			line_noclass = [lcontext,rcontext,cl];		
			line_withclass = [lcontext,cl,rcontext,cl];
			line_err = [lcontext,cl,rcontext,cl];

		#Output
		output['noclass'][use].write(' '.join(line_noclass)+'\n');
		output['withclass'][use].write(' '.join(line_withclass)+'\n');
		output['err'][use].write(' '.join(line_err)+'\n');
