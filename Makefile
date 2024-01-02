.PHONY: clean run

dep:
	pip install -r requirements.txt
debug: dep
	python -m pdb wenku8.py
run: dep
	python wenku8.py
clean:
	@rm -rf 第*卷*