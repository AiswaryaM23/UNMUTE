from servies.collect_finetune_data import main as fine_tune_data
from servies.retrain_mixed import main as retrain

print("Finetunning starting............")
fine_tune_data()
print("Stopping fineTunning............")
print("starting retraining.............")
retrain()
print("Complete retraining.............")