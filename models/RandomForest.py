'''
created on Mar 29, 2015

@author: epaul626
'''
import numpy as np
import sys, time
from optparse import OptionParser
from sklearn.ensemble import RandomForestRegressor
sys.path.append('../utils/')
#import UtilityFunctions
from UtilityFunctions import *
from FillData import *

# Treats each CpG site at each sample as its own sample
# Rather than as features for a given CpG site
def feat_all_samples(sites, train_beta, sample, test):
# 5 X features
# Feature 1: CpG start site
# Feature 2: distance to neighbor 1
# Feature 3: beta at neighbor 1
# Feature 4: distance to neighbor 2
# Feature 5: beta at neighbor 2
# Y: Beta value at sample site
	X = sites_beta_to_feat(sites, train_beta)
	Y = sites_beta_to_feat(sites, train_beta, True)
	# Predict on feature set not on 450k chip
	Xstar = sample[sample['450k']==0]
	gTruth = test[sample['450k']==0]
	Xstar = sites_beta_to_feat(Xstar['Start'], Xstar['Beta'])
	Xstar = Xstar[~np.isnan(gTruth)]
	gTruth = gTruth[~np.isnan(gTruth)]
	gTruth = gTruth[~np.isnan(Xstar[:,2])]
	gTruth = gTruth[~np.isnan(Xstar[:,4])]
	Xstar = Xstar[~np.isnan(Xstar[:,2])]
	Xstar = Xstar[~np.isnan(Xstar[:,4])]

	# Only train on non-NaN values of X & Y
	X = X[~np.isnan(Y)]
	Y = Y[~np.isnan(Y)]
	Y = Y[~np.isnan(X[:,2])]
	Y = Y[~np.isnan(X[:,4])]
	X = X[~np.isnan(X[:,2])]
	X = X[~np.isnan(X[:,4])]
	return (X, Y, Xstar, gTruth)

# Produces 'X' feature array of nearest neighbor beta values that will be fed
# into regressor
# Beta is an array of shape (# of CpG sites, nsamples)
# Sites is an array of shape (# of CpG sites, 2) corresponding to 
# start and ending bp of site
def feat_neighbors(sites, train_beta, sample, test):
	X = np.zeros((len(train_beta), 38))
	for i in range(0, len(train_beta)):
		# Feature 1: CpG start site
		X[i,0] = sites[i]
                # Find 2 nearest neighbors to site i
                (indices,distance)  = find_neighbors(sites, i)
                index1 = indices[0]
                index2 = indices[1]
		for j in range(0, 33):
			# Feature 2: beta at neighbor 1
			X[i, 1] = train_beta[i+index1, j]
			# Feature 3: distance to neighbor 1
			X[i, 2] = distance[0]
			# Feature 4: beta at neighbor 2
			X[i, 3] = train_beta[i+index2, j]
			# Feature 5: distance to neighbor 2
			X[i, 4] = distance[1]
			# Features 6-38: 33 sample beta values at CpG site
			X[i, 5+j] = train_beta[i, j]
	# Predict on feature set not on 450k chip
	Xstar = X[sample['450k']==0]
    	gTruth = test['Beta'][sample['450k']==0]
    	Xstar = Xstar[~np.isnan(gTruth)]
   	gTruth = gTruth[~np.isnan(gTruth)]

        # Only train on non-NaN values of Y
        X = X[~np.isnan(sample['Beta'])]
        Y = sample['Beta'][~np.isnan(sample['Beta'])]
	return (X, Y, Xstar, gTruth)

# Produces 'X' feature array of nearest neighbor beta values that will be fed
# into regressor
# Beta is an array of shape (# of CpG sites, nsamples)
# Sites is an array of shape (# of CpG sites, 2) corresponding to 
# start and ending bp of site
def feat_neighbors_islands(sites, train_island, train_beta, sample, test):
        X = np.zeros((len(train_beta), 39))
        for i in range(0, len(train_beta)):
                # Feature 1: CpG start site
                X[i,0] = sites[i]
                # Find 2 nearest neighbors to site i
                (indices,distance)  = find_neighbors(sites, i)
                index1 = indices[0]
                index2 = indices[1]
                for j in range(0, 33):
                        # Feature 2: beta at neighbor 1
                        X[i, 1] = train_beta[i+index1, j]
                        # Feature 3: distance to neighbor 1
                        X[i, 2] = distance[0]
                        # Feature 4: beta at neighbor 2
                        X[i, 3] = train_beta[i+index2, j]
                        # Feature 5: distance to neighbor 2
                        X[i, 4] = distance[1]
			# Feature 6: CpG site boolean
			X[i, 5] = train_island[i]
                        # Features 6-38: 33 sample beta values at CpG site
                        X[i, 5+j] = train_beta[i, j]
        # Predict on feature set not on 450k chip
        Xstar = X[sample['450k']==0]
        gTruth = test['Beta'][sample['450k']==0]
	Xstar = Xstar[~np.isnan(gTruth)]
        gTruth = gTruth[~np.isnan(gTruth)]

        # Only train on non-NaN values of Y
        X = X[~np.isnan(sample['Beta'])]
        Y = sample['Beta'][~np.isnan(sample['Beta'])]
        return (X, Y, Xstar, gTruth)

# Find nearest 2 sites to current CpG site
# Returns list of indices of 2 nearest neighbors
# Where the index in 'sites' is i + (index1, index2)
def find_neighbors(sites, i):
	curr = sites[i]
	if (i > 0):
		d_l1 = curr - sites[i-1]
	if (i > 1):
		d_l2 = curr - sites[i-2]
	if (i < len(sites)-1):
		d_r1 = sites[i+1] - curr
	if (i < len(sites)-2):
		d_r2 = sites[i+2] - curr
	# Look to left
	if (i == 0):
		return ([1, 2], [d_r1, d_r2])
	if (i == 1):
		d_l2 = -1
	# Look to right
	if (i == len(sites)-1):
		return ([-1, -2], [d_l1, d_l2])
	if (i == len(sites)-2):
		d_r2 = -1
	# Compare distances
	if (d_l1 < d_r1 and d_l1 != -1):
		if (d_l2 < d_r1):
			return ([-1, -2], [d_l1, d_l2])
		else:
			return ([-1, 1], [d_l1, d_r1])
	if (d_r2 < d_l1 and d_r2 != -1):
		return ([1, 2], [d_r1, d_r2])
	else:
		return ([1, -1], [d_r1, d_l1])
 
def main(argv):
	parser = OptionParser()
	parser.add_option("-p", "--path", dest="path", help='read bed data fom PATH', metavar='PATH')
	(options, args) = parser.parse_args()
	path = options.path
	start_time = time.time()

	# Read in data on islands
        island_start = time.time()
        train = read_bed_dat_train(path, Island=True)
        sample = read_bed_dat_sample(path, Island=True)
        test = read_bed_dat_test(path, Island=True)
        sites = train['Start']
# Fill in NaNs in training with mean over 33 samples in training bed
        #train_beta = fill_neighbors(sites, train['Beta'], 10)
	#train_beta = fill_rand(train['Beta'])
	train_beta = fill_mean(train['Beta'])
# Produce feature array 'X' and vector of beta values 'Y'
# Produce feature array 'X*' to predict on and ground truth beta values 'Y*'
        (X, Y, Xstar, Ystar) = feat_neighbors(sites.copy(), train_beta.copy(), sample.copy(), test.copy())
        # Initialize regressor with default parameters
        model = RandomForestRegressor()
# Fit regressor using training data
        model.fit(X, Y)
# Predict on Xstar values 
        Yhat = model.predict(Xstar)
# Calculate r2 and RMSE
        (r2, RMSE) = calc_r2_RMSE(Yhat, Ystar)
        print "Intersects with CGIs"
        print "Runtime: %f" % (time.time()-island_start)
        print "RandomForest Runtime: %f" % (time.time()-start_time)
        print "r2 : %f" % (r2)
        print "RMSE: %f" % (RMSE)

# use island feature set
        island_start = time.time()
        train = read_bed_dat_train(path, addIsland=True)
        sample = read_bed_dat_sample(path, addIsland=True)
        test = read_bed_dat_test(path, addIsland=True)
        sites = train['Start']
# Fill in NaNs in training with mean over 33 samples in training bed
        #train_beta = fill_neighbors(sites, train['Beta'], 10)
	#train_beta = fill_rand(train['Beta'])
	train_beta = fill_mean(train['Beta'])
	train_island = train['Island']
# Produce feature array 'X' and vector of beta values 'Y'
# Produce feature array 'X*' to predict on and ground truth beta values 'Y*'
	(X, Y, Xstar, Ystar) = feat_neighbors_islands(sites.copy(), train_island.copy(), train_beta.copy(), sample.copy(), test.copy())
        # Initialize regressor with default parameters
        model = RandomForestRegressor()
# Fit regressor using training data
        model.fit(X, Y)
# Predict on Xstar values 
        Yhat = model.predict(Xstar)
# Calculate r2 and RMSE
        (r2, RMSE) = calc_r2_RMSE(Yhat, Ystar)
        print "Island feature set"
        print "Runtime: %f" % (time.time()-island_start)
        print "RandomForest Runtime: %f" % (time.time()-start_time)
        print "r2 : %f" % (r2)
        print "RMSE: %f" % (RMSE)


# Read in data
        train = read_bed_dat_train(path)
	sample = read_bed_dat_sample(path)
	test = read_bed_dat_test(path)
	sites = train['Start']
# Fill in NaNs in training with mean over 33 samples in training bed
	#train_beta = fill_neighbors(sites, train['Beta'], 10)
	#train_beta = fill_rand(train['Beta'])
	train_beta = fill_mean(train['Beta'])
# Produce feature array 'X' and vector of beta values 'Y'
# Produce feature array 'X*' to predict on and ground truth beta values 'Y*'
	(X, Y, Xstar, Ystar) = feat_neighbors(sites.copy(), train_beta.copy(), sample.copy(), test.copy())
# Initialize regressor with default parameters
	start_rf = time.time()
	model = RandomForestRegressor()
# Fit regressor using training data
	model.fit(X, Y)
# Predict on Xstar values 
	Yhat = model.predict(Xstar)
# Calculate r2 and RMSE
        (r2, RMSE) = calc_r2_RMSE(Yhat, Ystar)
	print "Standard Feature Set"
	print "Runtime: %f" % (time.time()-start_time)
	print "RandomForest Runtime: %f" % (time.time()-start_rf)
	print "r2 : %f" % (r2)
	print "RMSE: %f" % (RMSE)

if __name__ == '__main__':
    main(sys.argv[1:])
