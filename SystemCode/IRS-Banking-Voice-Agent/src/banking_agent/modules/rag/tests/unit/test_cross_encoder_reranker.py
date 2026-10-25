import unittest
from unittest.mock import Mock
import sys
import numpy as np
from banking_agent.modules.rag.cross_encoder_reranker import CrossEncoderReranker

class RerankerTests(unittest.TestCase):
    def setUp(self):
        self.model=Mock()
        self.reranker=CrossEncoderReranker(model=self.model)
        self.docs=[dict(document_id=str(i),title='Title',source='Policy',score=100-i,excerpt='Full evidence\n'+'content '*100) for i in range(3)]

    def test_scores_change_only_order_and_score(self):
        self.model.predict.return_value=np.array([-5.,-1.,-3.])
        result=self.reranker.rerank('query',self.docs,2)
        self.assertEqual([d['document_id'] for d in result],['1','2'])
        self.assertEqual(result[0]['excerpt'],self.docs[1]['excerpt'])
        self.assertEqual(self.docs[1]['score'],99)
        self.assertEqual(self.model.predict.call_args.args[0][0],('query','Title\n'+self.docs[0]['excerpt']))

    def test_empty_invalid_duplicate_and_nonfinite(self):
        self.assertEqual(self.reranker.rerank('query',[]),[])
        self.model.predict.assert_not_called()
        for query,k in [('',5),('query',True),('query',0)]:
            with self.assertRaises(ValueError):self.reranker.rerank(query,self.docs,k)
        with self.assertRaises(ValueError):self.reranker.rerank('query',[self.docs[0]]*2)
        for scores in ([1,2],[1,float('nan'),2],[[1],[2],[3]]):
            self.model.predict.return_value=np.array(scores)
            with self.assertRaises(ValueError):self.reranker.rerank('query',self.docs)

    def test_default_loader_uses_verified_pytorch_weights(self):
        factory = Mock(return_value=Mock())
        module = Mock(CrossEncoder=factory)
        with unittest.mock.patch.dict(sys.modules, {'sentence_transformers': module}):
            CrossEncoderReranker('model-id', revision='revision-id', local_files_only=True)
        self.assertEqual(factory.call_args.kwargs['model_kwargs'], {'use_safetensors': False})
