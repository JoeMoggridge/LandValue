This is a project to make some pretty plots of land value. 

# BristolPropertyPrices

My initial plan was to obtain price data from the Zoopla Api, and then figure out some way to subtract the value of the building. 

I ran into a few problems with this: 

1. the Zoopla API is capped at 100 calls an hour (for free users). Therefore, It would take too long to obtain data on the whole UK. 
Not to worry, lets only look at bristol. 
2. Because of the rate cap, development was torturously slow. 
3. I cant find information on the value of the buildings. 
Even if I could, I can't think of a way to link that info to transactions which Zoopla knows about

so, onto plan B...

# GovLandValueEstimates

I found a gov spreadsheet with estimates of land value. Plotting this should be relatively straightforward, and indeed it was. 
Some slight fiddling required in order to match the price data to the correct shape object, but mostly fine. 
