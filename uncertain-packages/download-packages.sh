#!/bin/bash
# Script to download uncertain packages for manual license inspection

mkdir -p downloaded-packages

# coverage 7.11.0
wget -q -O downloaded-packages/coverage-7.11.0.tar.gz "https://files.pythonhosted.org/packages/1c/38/ee22495420457259d2f3390309505ea98f98a5eed40901cf62196abad006/coverage-7.11.0.tar.gz" || echo "Failed to download coverage"

# iniconfig 2.3.0
wget -q -O downloaded-packages/iniconfig-2.3.0.tar.gz "https://files.pythonhosted.org/packages/72/34/14ca021ce8e5dfedc35312d08ba8bf51fdd999c576889fc2c24cb97f4f10/iniconfig-2.3.0.tar.gz" || echo "Failed to download iniconfig"

# numpy 2.3.4
wget -q -O downloaded-packages/numpy-2.3.4.tar.gz "https://files.pythonhosted.org/packages/b5/f4/098d2270d52b41f1bd7db9fc288aaa0400cb48c2a3e2af6fa365d9720947/numpy-2.3.4.tar.gz" || echo "Failed to download numpy"

# packaging 25.0
wget -q -O downloaded-packages/packaging-25.0.tar.gz "https://files.pythonhosted.org/packages/a1/d4/1fc4078c65507b51b96ca8f8c3ba19e6a61c8253c72794544580a7b6c24d/packaging-25.0.tar.gz" || echo "Failed to download packaging"

# pluggy 1.6.0
wget -q -O downloaded-packages/pluggy-1.6.0.tar.gz "https://files.pythonhosted.org/packages/f9/e2/3e91f31a7d2b083fe6ef3fa267035b518369d9511ffab804f839851d2779/pluggy-1.6.0.tar.gz" || echo "Failed to download pluggy"

# pycutest 1.7.2
wget -q -O downloaded-packages/pycutest-1.7.2.tar.gz "https://files.pythonhosted.org/packages/e8/af/b8ca11affc4df8d5c1e6526abffdab573582c47dc9ebe0ea00d0a1378f07/pycutest-1.7.2.tar.gz" || echo "Failed to download pycutest"

# pygments 2.19.2
wget -q -O downloaded-packages/pygments-2.19.2.tar.gz "https://files.pythonhosted.org/packages/b0/77/a5b8c569bf593b0140bde72ea885a803b82086995367bf2037de0159d924/pygments-2.19.2.tar.gz" || echo "Failed to download pygments"

# pytest 8.4.2
wget -q -O downloaded-packages/pytest-8.4.2.tar.gz "https://files.pythonhosted.org/packages/a3/5c/00a0e072241553e1a7496d638deababa67c5058571567b92a7eaa258397c/pytest-8.4.2.tar.gz" || echo "Failed to download pytest"

# pytest-cov 7.0.0
wget -q -O downloaded-packages/pytest-cov-7.0.0.tar.gz "https://files.pythonhosted.org/packages/5e/f7/c933acc76f5208b3b00089573cf6a2bc26dc80a8aece8f52bb7d6b1855ca/pytest_cov-7.0.0.tar.gz" || echo "Failed to download pytest-cov"

# pytest-order 1.3.0
wget -q -O downloaded-packages/pytest-order-1.3.0.tar.gz "https://files.pythonhosted.org/packages/1d/66/02ae17461b14a52ce5a29ae2900156b9110d1de34721ccc16ccd79419876/pytest_order-1.3.0.tar.gz" || echo "Failed to download pytest-order"

# scipy 1.16.3
wget -q -O downloaded-packages/scipy-1.16.3.tar.gz "https://files.pythonhosted.org/packages/0a/ca/d8ace4f98322d01abcd52d381134344bf7b431eba7ed8b42bdea5a3c2ac9/scipy-1.16.3.tar.gz" || echo "Failed to download scipy"

# setuptools 80.9.0
wget -q -O downloaded-packages/setuptools-80.9.0.tar.gz "https://files.pythonhosted.org/packages/18/5d/3bf57dcd21979b887f014ea83c24ae194cfcd12b9e0fda66b957c69d1fca/setuptools-80.9.0.tar.gz" || echo "Failed to download setuptools"

